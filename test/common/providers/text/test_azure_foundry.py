import pytest
from unittest.mock import Mock, PropertyMock
from common.providers.text.azure_foundry import AzureFoundryTextProvider


@pytest.fixture
def mock_azure_client():
    return Mock()


@pytest.fixture
def mock_channel():
    channel = Mock()
    type(channel).system_prompt = PropertyMock(return_value="You are a Pinterest expert.")
    return channel


@pytest.fixture
def provider(mock_azure_client):
    return AzureFoundryTextProvider(mock_azure_client)


def test_generate_text_success(provider, mock_azure_client, mock_channel):
    """Test successful text generation returns parsed JSON dict"""
    # Setup mock response
    mock_response = Mock()
    mock_message = Mock()
    mock_choice = Mock()

    mock_message.content = '{"title": "Amazing Pinterest Pin", "description": "Discover the best tips for your niche!", "cta": "Click to learn more"}'
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_azure_client.chat.completions.create.return_value = mock_response

    # Execute
    result = provider.generate_text(
        niche="Home Decor", keyword="DIY Projects", channel=mock_channel
    )

    # Assertions
    assert result == {
        "title": "Amazing Pinterest Pin",
        "description": "Discover the best tips for your niche!",
        "cta": "Click to learn more"
    }

    # Verify API was called with correct parameters
    mock_azure_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_azure_client.chat.completions.create.call_args.kwargs

    assert call_kwargs["model"] == "gpt-5-nano"
    assert call_kwargs["max_completion_tokens"] == 16000
    assert len(call_kwargs["messages"]) == 2
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][0]["content"] == mock_channel.system_prompt
    assert call_kwargs["messages"][1]["role"] == "user"
    assert "Home Decor" in call_kwargs["messages"][1]["content"]
    assert "DIY Projects" in call_kwargs["messages"][1]["content"]
