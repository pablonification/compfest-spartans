"""Unit tests for scan router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from src.backend.routers.scan import router
from src.backend.models.user import User
from src.backend.services.opencv_service import MeasurementError


class TestScanRouter:
    """Test cases for scan router."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        return User(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            points=100,
            google_id="google_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            scan_ids=["scan1", "scan2"]
        )

    @pytest.fixture
    def mock_image_file(self):
        """Create a mock image file for testing."""
        file = Mock(spec=UploadFile)
        file.read = AsyncMock(return_value=b"fake_image_data")
        file.filename = "test_image.jpg"
        return file

    @pytest.fixture
    def mock_measurement(self):
        """Create a mock measurement result."""
        measurement = Mock()
        measurement.diameter_mm = 65.0
        measurement.height_mm = 180.0
        measurement.volume_ml = 600.0
        measurement.__dict__ = {
            "diameter_mm": 65.0,
            "height_mm": 180.0,
            "volume_ml": 600.0
        }
        return measurement

    @pytest.fixture
    def mock_validation_result(self):
        """Create a mock validation result."""
        validation_result = Mock()
        validation_result.is_valid = True
        validation_result.brand = "aqua"
        validation_result.confidence = 0.95
        validation_result.points_awarded = 10
        validation_result.reason = "Valid bottle"
        validation_result.measurement = mock_measurement
        return validation_result

    @pytest.fixture
    def mock_iot_events(self):
        """Create mock IoT events."""
        return ["lid_opened", "sensor_triggered", "lid_closed"]

    @pytest.fixture
    def mock_mongo_result(self):
        """Create a mock MongoDB insert result."""
        result = Mock()
        result.inserted_id = "scan_id_123"
        return result

    @pytest.mark.asyncio
    async def test_scan_bottle_success(self, mock_user, mock_image_file, mock_measurement, 
                                     mock_validation_result, mock_iot_events, mock_mongo_result):
        """Test successful bottle scanning."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", return_value={"predictions": []}), \
             patch("src.backend.routers.scan.validate_scan", return_value=mock_validation_result), \
             patch("src.backend.routers.scan.smartbin_client.open_bin", return_value=mock_iot_events), \
             patch("src.backend.routers.scan.add_points", return_value=110), \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock MongoDB
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.return_value = mock_mongo_result
            
            # Mock user service
            mock_user_service = AsyncMock()
            mock_get_user_service.return_value = mock_user_service
            
            # Mock WebSocket manager
            mock_manager.broadcast = AsyncMock()
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = True
            
            # Create request context
            request = Mock()
            request.state.user = mock_user
            
            # Call the scan function
            from src.backend.routers.scan import scan_bottle
            result = await scan_bottle(request, mock_image_file, mock_user)
            
            # Verify the result
            assert result.is_valid is True
            assert result.brand == "aqua"
            assert result.confidence == 0.95
            assert result.points_awarded == 10
            assert result.total_points == 110
            
            # Verify MongoDB was called
            mock_db.__getitem__.assert_called_with("scans")
            mock_db.__getitem__.return_value.insert_one.assert_called_once()
            
            # Verify WebSocket broadcasts
            mock_manager.broadcast.assert_called_once()
            mock_manager.broadcast_to_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_bottle_empty_image(self, mock_user, mock_image_file):
        """Test scanning with empty image."""
        mock_image_file.read.return_value = b""
        
        with pytest.raises(HTTPException) as exc_info:
            from src.backend.routers.scan import scan_bottle
            request = Mock()
            request.state.user = mock_user
            await scan_bottle(request, mock_image_file, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Empty image upload" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_scan_bottle_measurement_failure(self, mock_user, mock_image_file):
        """Test scanning when measurement fails."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", 
                  side_effect=MeasurementError("Measurement failed")):
            
            with pytest.raises(HTTPException) as exc_info:
                from src.backend.routers.scan import scan_bottle
                request = Mock()
                request.state.user = mock_user
                await scan_bottle(request, mock_image_file, mock_user)
            
            assert exc_info.value.status_code == 422
            assert "Unable to measure bottle" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_scan_bottle_roboflow_failure(self, mock_user, mock_image_file, mock_measurement):
        """Test scanning when Roboflow fails."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", 
                  side_effect=Exception("Roboflow error")):
            
            with pytest.raises(HTTPException) as exc_info:
                from src.backend.routers.scan import scan_bottle
                request = Mock()
                request.state.user = mock_user
                await scan_bottle(request, mock_image_file, mock_user)
            
            assert exc_info.value.status_code == 502
            assert "Error contacting AI service" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_scan_bottle_invalid_bottle(self, mock_user, mock_image_file, mock_measurement):
        """Test scanning an invalid bottle."""
        mock_validation_result = Mock()
        mock_validation_result.is_valid = False
        mock_validation_result.brand = "unknown"
        mock_validation_result.confidence = 0.3
        mock_validation_result.points_awarded = 0
        mock_validation_result.reason = "Invalid bottle type"
        mock_validation_result.measurement = mock_measurement
        
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", return_value={"predictions": []}), \
             patch("src.backend.routers.scan.validate_scan", return_value=mock_validation_result), \
             patch("src.backend.routers.scan.add_points", return_value=100), \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager:
            
            # Mock MongoDB
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.return_value = mock_mongo_result
            
            # Mock WebSocket manager
            mock_manager.broadcast = AsyncMock()
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = False
            
            # Create request context
            request = Mock()
            request.state.user = mock_user
            
            # Call the scan function
            from src.backend.routers.scan import scan_bottle
            result = await scan_bottle(request, mock_image_file, mock_user)
            
            # Verify the result
            assert result.is_valid is False
            assert result.brand == "unknown"
            assert result.confidence == 0.3
            assert result.points_awarded == 0
            assert result.total_points == 100  # No points added for invalid bottle

    @pytest.mark.asyncio
    async def test_scan_bottle_points_addition_failure(self, mock_user, mock_image_file, mock_measurement, 
                                                    mock_validation_result, mock_iot_events):
        """Test scanning when points addition fails."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", return_value={"predictions": []}), \
             patch("src.backend.routers.scan.validate_scan", return_value=mock_validation_result), \
             patch("src.backend.routers.scan.smartbin_client.open_bin", return_value=mock_iot_events), \
             patch("src.backend.routers.scan.add_points", side_effect=Exception("Points error")), \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager:
            
            # Mock MongoDB
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.return_value = mock_mongo_result
            
            # Mock WebSocket manager
            mock_manager.broadcast = AsyncMock()
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = False
            
            # Create request context
            request = Mock()
            request.state.user = mock_user
            
            # Call the scan function
            from src.backend.routers.scan import scan_bottle
            result = await scan_bottle(request, mock_image_file, mock_user)
            
            # Verify the result - should continue with current points
            assert result.is_valid is True
            assert result.total_points == 100  # Current user points

    @pytest.mark.asyncio
    async def test_scan_bottle_mongodb_failure(self, mock_user, mock_image_file, mock_measurement, 
                                             mock_validation_result, mock_iot_events):
        """Test scanning when MongoDB save fails."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", return_value={"predictions": []}), \
             patch("src.backend.routers.scan.validate_scan", return_value=mock_validation_result), \
             patch("src.backend.routers.scan.smartbin_client.open_bin", return_value=mock_iot_events), \
             patch("src.backend.routers.scan.add_points", return_value=110), \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager:
            
            # Mock MongoDB failure
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.side_effect = Exception("MongoDB error")
            
            # Mock WebSocket manager
            mock_manager.broadcast = AsyncMock()
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = False
            
            # Create request context
            request = Mock()
            request.state.user = mock_user
            
            # Call the scan function - should not raise exception
            from src.backend.routers.scan import scan_bottle
            result = await scan_bottle(request, mock_image_file, mock_user)
            
            # Verify the result - should still work
            assert result.is_valid is True
            assert result.total_points == 110

    @pytest.mark.asyncio
    async def test_scan_bottle_websocket_failure(self, mock_user, mock_image_file, mock_measurement, 
                                               mock_validation_result, mock_iot_events, mock_mongo_result):
        """Test scanning when WebSocket broadcast fails."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", return_value={"predictions": []}), \
             patch("src.backend.routers.scan.validate_scan", return_value=mock_validation_result), \
             patch("src.backend.routers.scan.smartbin_client.open_bin", return_value=mock_iot_events), \
             patch("src.backend.routers.scan.add_points", return_value=110), \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager:
            
            # Mock MongoDB
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.return_value = mock_mongo_result
            
            # Mock WebSocket manager failure
            mock_manager.broadcast.side_effect = Exception("WebSocket error")
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = False
            
            # Create request context
            request = Mock()
            request.state.user = mock_user
            
            # Call the scan function - should not raise exception
            from src.backend.routers.scan import scan_bottle
            result = await scan_bottle(request, mock_image_file, mock_user)
            
            # Verify the result - should still work
            assert result.is_valid is True
            assert result.total_points == 110

    @pytest.mark.asyncio
    async def test_scan_bottle_user_scan_history_update(self, mock_user, mock_image_file, mock_measurement, 
                                                      mock_validation_result, mock_iot_events, mock_mongo_result):
        """Test that scan ID is added to user's scan history."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", return_value={"predictions": []}), \
             patch("src.backend.routers.scan.validate_scan", return_value=mock_validation_result), \
             patch("src.backend.routers.scan.smartbin_client.open_bin", return_value=mock_iot_events), \
             patch("src.backend.routers.scan.add_points", return_value=110), \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock MongoDB
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.return_value = mock_mongo_result
            
            # Mock user service
            mock_user_service = AsyncMock()
            mock_get_user_service.return_value = mock_user_service
            
            # Mock WebSocket manager
            mock_manager.broadcast = AsyncMock()
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = False
            
            # Create request context
            request = Mock()
            request.state.user = mock_user
            
            # Call the scan function
            from src.backend.routers.scan import scan_bottle
            result = await scan_bottle(request, mock_image_file, mock_user)
            
            # Verify user service was called to add scan to history
            mock_user_service.add_scan_to_user.assert_called_once_with("test_user_id", "scan_id_123")

    @pytest.mark.asyncio
    async def test_scan_bottle_scan_history_update_failure(self, mock_user, mock_image_file, mock_measurement, 
                                                         mock_validation_result, mock_iot_events, mock_mongo_result):
        """Test that scan continues even when scan history update fails."""
        with patch("src.backend.routers.scan.bottle_measurer.measure", return_value=mock_measurement), \
             patch("src.backend.routers.scan.roboflow_client.predict", return_value={"predictions": []}), \
             patch("src.backend.routers.scan.validate_scan", return_value=mock_validation_result), \
             patch("src.backend.routers.scan.smartbin_client.open_bin", return_value=mock_iot_events), \
             patch("src.backend.routers.scan.add_points", return_value=110), \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock MongoDB
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.return_value = mock_mongo_result
            
            # Mock user service failure
            mock_user_service = AsyncMock()
            mock_user_service.add_scan_to_user.side_effect = Exception("History update error")
            mock_get_user_service.return_value = mock_user_service
            
            # Mock WebSocket manager
            mock_manager.broadcast = AsyncMock()
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = False
            
            # Create request context
            request = Mock()
            request.state.user = mock_user
            
            # Call the scan function - should not raise exception
            from src.backend.routers.scan import scan_bottle
            result = await scan_bottle(request, mock_image_file, mock_user)
            
            # Verify the result - should still work
            assert result.is_valid is True
            assert result.total_points == 110
