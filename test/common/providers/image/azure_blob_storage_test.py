import pytest
from unittest.mock import Mock, MagicMock, patch
from common.providers.image.azure_blob_storage import AzureBlobStorageImageProvider
from common.contracts.database_models import Keyword


@pytest.fixture
def mock_blob_client():
    return Mock()


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def provider(mock_blob_client, mock_logger):
    return AzureBlobStorageImageProvider(mock_blob_client, mock_logger)


@pytest.fixture
def mock_keyword():
    keyword = Mock(spec=Keyword)
    keyword.keyword_id = 123
    keyword.name = "test_keyword"
    return keyword


def test_fetch_image_success(provider, mock_blob_client, mock_keyword, mock_logger):
    """Test successful image fetch returns blob URL"""
    # Setup mocks
    mock_container_client = Mock()
    mock_blob_client.get_container_client.return_value = mock_container_client
    mock_container_client.url = "https://storage.blob.core.windows.net/images"

    # Mock blob objects
    mock_blob1 = Mock()
    mock_blob1.name = "keywords/123/image1.jpg"
    mock_blob2 = Mock()
    mock_blob2.name = "keywords/123/image2.png"

    mock_container_client.list_blobs.return_value = [mock_blob1, mock_blob2]

    # Patch random.choice to be deterministic
    with patch('common.providers.image.azure_blob_storage.random.choice', return_value=mock_blob1):
        result = provider.fetch_image(mock_keyword)

    # Assertions
    assert result == "https://storage.blob.core.windows.net/images/keywords/123/image1.jpg"
    mock_blob_client.get_container_client.assert_called_once_with("images")
    mock_container_client.list_blobs.assert_called_once_with(name_starts_with="keywords/123/")
    mock_logger.info.assert_called_once()


def test_fetch_image_no_images_raises_error(provider, mock_blob_client, mock_keyword, mock_logger):
    """Test that ValueError is raised when no images found"""
    # Setup mocks
    mock_container_client = Mock()
    mock_blob_client.get_container_client.return_value = mock_container_client
    mock_container_client.list_blobs.return_value = []

    # Assert exception is raised
    with pytest.raises(ValueError, match="No images found for keyword test_keyword"):
        provider.fetch_image(mock_keyword)

    # Verify error was logged
    mock_logger.error.assert_called()


def test_fetch_image_filters_txt_files(provider, mock_blob_client, mock_keyword):
    """Test that .txt files are filtered out from image selection"""
    # Setup mocks
    mock_container_client = Mock()
    mock_blob_client.get_container_client.return_value = mock_container_client
    mock_container_client.url = "https://storage.blob.core.windows.net/images"

    # Mock blob objects including .txt file
    mock_blob_image = Mock()
    mock_blob_image.name = "keywords/123/image1.jpg"
    mock_blob_txt = Mock()
    mock_blob_txt.name = "keywords/123/metadata.txt"

    mock_container_client.list_blobs.return_value = [mock_blob_image, mock_blob_txt]

    # Patch random.choice to verify only image was considered
    with patch('common.providers.image.azure_blob_storage.random.choice', return_value=mock_blob_image) as mock_choice:
        result = provider.fetch_image(mock_keyword)

        # Verify only non-txt file was passed to random.choice
        call_args = mock_choice.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].name == "keywords/123/image1.jpg"
        assert not result.endswith('.txt')
