"""
Comprehensive test suite for Vertex AI adapter with full mocking.

This module provides complete test coverage for Vertex AI client initialization,
embedding generation, LLM operations, batch processing, error handling, and
retry logic using fully mocked Vertex AI services.
"""

from __future__ import annotations

import pytest
from typing import Any, Generator, Optional
from unittest.mock import MagicMock, Mock, patch, PropertyMock
import time

from atoms_mcp.adapters.secondary.vertex.client import (
    VertexAIClient,
    VertexAIClientError,
    get_client,
    reset_client,
)
from atoms_mcp.adapters.secondary.vertex.embeddings import (
    TextEmbedder,
    EmbeddingError,
)
from atoms_mcp.adapters.secondary.vertex.llm import (
    LLMPrompt,
    ConversationManager,
    LLMError,
)


# ============================================================================
# Mock Vertex AI Implementation
# ============================================================================


class MockEmbedding:
    """Mock embedding response."""

    def __init__(self, values: list[float]):
        self.values = values


class MockTextEmbeddingModel:
    """Mock Vertex AI text embedding model."""

    def __init__(
        self,
        model_name: str = "textembedding-gecko@003",
        should_fail: bool = False,
        failure_count: int = 0,
    ):
        self.model_name = model_name
        self.should_fail = should_fail
        self.failure_count = failure_count
        self.call_count = 0
        self.call_log: list[tuple[str, Any]] = []

    def get_embeddings(self, inputs: list) -> list[MockEmbedding]:
        """Generate mock embeddings."""
        self.call_count += 1
        self.call_log.append(("get_embeddings", inputs))

        # Simulate transient failures
        if self.should_fail and self.call_count <= self.failure_count:
            from google.api_core.exceptions import ServiceUnavailable

            raise ServiceUnavailable("Service temporarily unavailable")

        # Generate mock embeddings
        return [MockEmbedding([0.1, 0.2, 0.3] * 256) for _ in inputs]

    @classmethod
    def from_pretrained(cls, model_name: str) -> MockTextEmbeddingModel:
        """Create model instance."""
        return cls(model_name=model_name)


class MockGenerativeModelResponse:
    """Mock response from generative model."""

    def __init__(self, text: str):
        self.text = text


class MockGenerativeModel:
    """Mock Vertex AI generative model."""

    def __init__(
        self,
        model_name: str = "gemini-1.5-pro",
        system_instruction: Optional[str] = None,
        should_fail: bool = False,
        failure_count: int = 0,
    ):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.should_fail = should_fail
        self.failure_count = failure_count
        self.call_count = 0
        self.call_log: list[tuple[str, Any]] = []

    def generate_content(
        self,
        prompt: str,
        generation_config: Any = None,
        stream: bool = False,
    ) -> Any:
        """Generate mock content."""
        self.call_count += 1
        self.call_log.append(("generate_content", prompt, generation_config))

        # Simulate transient failures
        if self.should_fail and self.call_count <= self.failure_count:
            from google.api_core.exceptions import ResourceExhausted

            raise ResourceExhausted("Rate limit exceeded")

        if stream:
            return self._generate_stream(prompt)
        else:
            return MockGenerativeModelResponse(f"Response to: {prompt}")

    def _generate_stream(self, prompt: str) -> Generator[MockGenerativeModelResponse, None, None]:
        """Generate streaming response."""
        words = f"Streaming response to: {prompt}".split()
        for word in words:
            yield MockGenerativeModelResponse(word + " ")

    def start_chat(self, history: Optional[list] = None) -> MockChat:
        """Start a chat session."""
        return MockChat(self, history or [])

    def count_tokens(self, text: str) -> MockTokenCount:
        """Count tokens in text."""
        self.call_log.append(("count_tokens", text))
        # Simple mock: 1 token per 4 characters
        return MockTokenCount(len(text) // 4)


class MockChat:
    """Mock chat session."""

    def __init__(self, model: MockGenerativeModel, history: list):
        self.model = model
        self.history = history

    def send_message(
        self,
        message: str,
        generation_config: Any = None,
        stream: bool = False,
    ) -> Any:
        """Send message in chat."""
        return self.model.generate_content(message, generation_config, stream)


class MockTokenCount:
    """Mock token count response."""

    def __init__(self, total: int):
        self.total_tokens = total


class MockVertexAIClient:
    """
    Complete mock implementation of Vertex AI client.

    Features:
    - Initialization tracking
    - Configuration management
    - Error injection
    - Call logging
    """

    def __init__(self):
        self.initialized = False
        self.project_id = "test-project"
        self.location = "us-central1"
        self.model_name = "textembedding-gecko@003"
        self.max_retries = 3
        self.timeout = 30
        self.call_log: list[tuple[str, Any]] = []

    def init(self, project: str, location: str, credentials: Any = None):
        """Initialize Vertex AI."""
        self.initialized = True
        self.project_id = project
        self.location = location
        self.call_log.append(("init", project, location))


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_settings():
    """Mock settings for Vertex AI."""
    with patch("atoms_mcp.adapters.secondary.vertex.client.get_settings") as mock:
        settings = MagicMock()
        settings.vertex_ai.project_id = "test-project"
        settings.vertex_ai.location = "us-central1"
        settings.vertex_ai.model_name = "textembedding-gecko@003"
        settings.vertex_ai.credentials_path = None
        settings.vertex_ai.max_retries = 3
        settings.vertex_ai.timeout = 30
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_aiplatform():
    """Mock aiplatform module."""
    with patch("atoms_mcp.adapters.secondary.vertex.client.aiplatform") as mock:
        yield mock


@pytest.fixture
def mock_credentials():
    """Mock Google credentials."""
    with patch("atoms_mcp.adapters.secondary.vertex.client.google_auth_default") as mock:
        credentials = MagicMock()
        mock.return_value = (credentials, "test-project")
        yield credentials


@pytest.fixture
def vertex_client(mock_settings, mock_aiplatform, mock_credentials):
    """Provide a Vertex AI client with mocked dependencies."""
    client = VertexAIClient()
    yield client
    client.reset()


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model."""
    with patch("atoms_mcp.adapters.secondary.vertex.embeddings.TextEmbeddingModel") as mock:
        model = MockTextEmbeddingModel()
        mock.from_pretrained.return_value = model
        yield model


@pytest.fixture
def mock_generative_model():
    """Mock generative model."""
    with patch("atoms_mcp.adapters.secondary.vertex.llm.GenerativeModel") as mock:
        model = MockGenerativeModel()
        mock.return_value = model
        yield model


# ============================================================================
# Client Initialization Tests (10 tests)
# ============================================================================


class TestVertexAIClientInitialization:
    """Test Vertex AI client initialization and configuration."""

    def test_client_initialization_success(self, mock_settings, mock_aiplatform, mock_credentials):
        """
        Given: Valid Vertex AI configuration
        When: Creating a new client
        Then: Client is initialized successfully
        """
        client = VertexAIClient()

        assert client.is_initialized()
        assert client.project_id == "test-project"
        assert client.location == "us-central1"
        mock_aiplatform.init.assert_called_once()

    def test_client_initialization_missing_project_id(self, mock_settings, mock_aiplatform):
        """
        Given: Missing project ID in configuration
        When: Attempting to create client
        Then: VertexAIClientError is raised
        """
        mock_settings.vertex_ai.project_id = None

        with pytest.raises(VertexAIClientError, match="project_id is not configured"):
            VertexAIClient()

    def test_client_singleton_pattern(self, vertex_client):
        """
        Given: An existing client instance
        When: Creating another client
        Then: Same instance is returned (singleton)
        """
        client1 = VertexAIClient()
        client2 = VertexAIClient()

        assert client1 is client2

    def test_client_properties(self, vertex_client):
        """
        Given: Initialized client
        When: Accessing properties
        Then: Correct values are returned
        """
        assert vertex_client.project_id == "test-project"
        assert vertex_client.location == "us-central1"
        assert vertex_client.model_name == "textembedding-gecko@003"
        assert vertex_client.max_retries == 3
        assert vertex_client.timeout == 30

    def test_client_with_credentials_file(self, mock_settings, mock_aiplatform):
        """
        Given: Credentials file path is provided
        When: Initializing client
        Then: Credentials are loaded from file
        """
        mock_settings.vertex_ai.credentials_path = "/path/to/credentials.json"

        with patch("atoms_mcp.adapters.secondary.vertex.client.service_account") as mock_sa:
            mock_creds = MagicMock()
            mock_sa.Credentials.from_service_account_file.return_value = mock_creds

            client = VertexAIClient()

            mock_sa.Credentials.from_service_account_file.assert_called_once()
            assert client.is_initialized()

    def test_client_with_default_credentials(self, mock_settings, mock_aiplatform, mock_credentials):
        """
        Given: No credentials file provided
        When: Initializing client
        Then: Default credentials are used
        """
        mock_settings.vertex_ai.credentials_path = None

        client = VertexAIClient()

        assert client.is_initialized()

    def test_client_credentials_error(self, mock_settings, mock_aiplatform):
        """
        Given: Invalid credentials file
        When: Attempting to initialize client
        Then: VertexAIClientError is raised
        """
        mock_settings.vertex_ai.credentials_path = "/invalid/path.json"

        with patch("atoms_mcp.adapters.secondary.vertex.client.service_account") as mock_sa:
            mock_sa.Credentials.from_service_account_file.side_effect = Exception("File not found")

            with pytest.raises(VertexAIClientError, match="Failed to load credentials"):
                VertexAIClient()

    def test_client_reset(self, vertex_client):
        """
        Given: Initialized client
        When: Resetting the client
        Then: Client state is cleared
        """
        assert vertex_client.is_initialized()

        vertex_client.reset()

        assert not vertex_client.is_initialized()

    def test_client_property_not_initialized(self):
        """
        Given: Client not initialized
        When: Accessing properties
        Then: VertexAIClientError is raised
        """
        client = object.__new__(VertexAIClient)
        client._initialized = False
        client._settings = None

        with pytest.raises(VertexAIClientError, match="not initialized"):
            _ = client.project_id

    def test_global_client_getter(self, mock_settings, mock_aiplatform, mock_credentials):
        """
        Given: No existing global client
        When: Calling get_client
        Then: Global client is created and returned
        """
        reset_client()

        client1 = get_client()
        client2 = get_client()

        assert client1 is client2


# ============================================================================
# Embedding Generation Tests (15 tests)
# ============================================================================


class TestEmbeddingGeneration:
    """Test text embedding generation."""

    @pytest.fixture
    def embedder(self, vertex_client, mock_embedding_model):
        """Provide a text embedder instance."""
        return TextEmbedder()

    def test_generate_embedding_success(self, embedder):
        """
        Given: Valid text input
        When: Generating embedding
        Then: Embedding vector is returned
        """
        text = "Test text for embedding"

        result = embedder.generate_embedding(text)

        assert isinstance(result, list)
        assert len(result) == 768  # 256 * 3
        assert all(isinstance(x, float) for x in result)

    def test_generate_embedding_with_task(self, embedder):
        """
        Given: Text with specific task type
        When: Generating embedding
        Then: Task type is used correctly
        """
        text = "Search query"
        task = "RETRIEVAL_QUERY"

        result = embedder.generate_embedding(text, task=task)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_embedding_with_title(self, embedder):
        """
        Given: Text with title for document
        When: Generating embedding
        Then: Title is included in request
        """
        text = "Document content"
        title = "Document Title"

        result = embedder.generate_embedding(
            text,
            task="RETRIEVAL_DOCUMENT",
            title=title,
        )

        assert isinstance(result, list)

    def test_generate_embedding_with_cache(self, embedder):
        """
        Given: Embedder with caching enabled
        When: Generating embedding twice for same text
        Then: Cached result is returned second time
        """
        embedder.cache_embeddings = True
        text = "Cached text"

        # First call
        result1 = embedder.generate_embedding(text)
        call_count_1 = embedder._get_model().call_count

        # Second call (should use cache)
        result2 = embedder.generate_embedding(text)
        call_count_2 = embedder._get_model().call_count

        assert result1 == result2
        assert call_count_2 == call_count_1  # No additional API call

    def test_generate_embedding_cache_different_tasks(self, embedder):
        """
        Given: Caching enabled with different tasks
        When: Generating embeddings for same text with different tasks
        Then: Different cache entries are created
        """
        embedder.cache_embeddings = True
        text = "Same text"

        result1 = embedder.generate_embedding(text, task="RETRIEVAL_QUERY")
        result2 = embedder.generate_embedding(text, task="RETRIEVAL_DOCUMENT")

        # Both should be cached separately
        assert embedder.get_cache_size() == 2

    def test_generate_embedding_retry_on_failure(self, vertex_client):
        """
        Given: Embedding model that fails once
        When: Generating embedding with retry
        Then: Successfully retries and returns result
        """
        with patch("atoms_mcp.adapters.secondary.vertex.embeddings.TextEmbeddingModel") as mock:
            model = MockTextEmbeddingModel(should_fail=True, failure_count=1)
            mock.from_pretrained.return_value = model

            with patch("atoms_mcp.adapters.secondary.vertex.embeddings.time.sleep"):
                embedder = TextEmbedder()
                result = embedder.generate_embedding("test")

                assert isinstance(result, list)
                assert model.call_count == 2  # Failed once, succeeded second time

    def test_generate_embedding_max_retries_exceeded(self, vertex_client):
        """
        Given: Embedding model that always fails
        When: Generating embedding
        Then: EmbeddingError is raised after max retries
        """
        with patch("atoms_mcp.adapters.secondary.vertex.embeddings.TextEmbeddingModel") as mock:
            model = MockTextEmbeddingModel(should_fail=True, failure_count=10)
            mock.from_pretrained.return_value = model

            with patch("atoms_mcp.adapters.secondary.vertex.embeddings.time.sleep"):
                embedder = TextEmbedder()

                with pytest.raises(EmbeddingError, match="after 3 attempts"):
                    embedder.generate_embedding("test")

    def test_generate_embeddings_batch_success(self, embedder):
        """
        Given: Multiple texts to embed
        When: Generating batch embeddings
        Then: All embeddings are returned
        """
        texts = ["text 1", "text 2", "text 3"]

        results = embedder.generate_embeddings_batch(texts)

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)

    def test_generate_embeddings_batch_with_titles(self, embedder):
        """
        Given: Texts with corresponding titles
        When: Generating batch embeddings
        Then: Titles are used for each embedding
        """
        texts = ["content 1", "content 2"]
        titles = ["title 1", "title 2"]

        results = embedder.generate_embeddings_batch(texts, titles=titles)

        assert len(results) == 2

    def test_generate_embeddings_batch_title_mismatch(self, embedder):
        """
        Given: Mismatched texts and titles lengths
        When: Generating batch embeddings
        Then: EmbeddingError is raised
        """
        texts = ["text 1", "text 2"]
        titles = ["title 1"]

        with pytest.raises(EmbeddingError, match="must match texts list length"):
            embedder.generate_embeddings_batch(texts, titles=titles)

    def test_generate_embeddings_batch_empty(self, embedder):
        """
        Given: Empty texts list
        When: Generating batch embeddings
        Then: Empty list is returned
        """
        results = embedder.generate_embeddings_batch([])

        assert results == []

    def test_generate_embeddings_batch_with_cache(self, embedder):
        """
        Given: Batch with some cached items
        When: Generating embeddings
        Then: Only uncached items are processed
        """
        embedder.cache_embeddings = True
        texts = ["cached", "uncached"]

        # Pre-cache first item
        embedder.generate_embedding(texts[0])
        initial_calls = embedder._get_model().call_count

        # Generate batch
        results = embedder.generate_embeddings_batch(texts)

        # Should only make one additional call for uncached item
        assert len(results) == 2

    def test_generate_embeddings_batch_size_limit(self, embedder):
        """
        Given: Large batch exceeding API limit
        When: Generating embeddings
        Then: Batch is automatically split
        """
        texts = [f"text {i}" for i in range(12)]

        results = embedder.generate_embeddings_batch(texts, batch_size=5)

        assert len(results) == 12

    def test_clear_cache(self, embedder):
        """
        Given: Embedder with cached items
        When: Clearing cache
        Then: Cache is emptied
        """
        embedder.cache_embeddings = True
        embedder.generate_embedding("test")

        assert embedder.get_cache_size() > 0

        embedder.clear_cache()

        assert embedder.get_cache_size() == 0

    def test_get_embedding_dimension(self, embedder):
        """
        Given: Configured embedding model
        When: Getting embedding dimension
        Then: Correct dimension is returned
        """
        dimension = embedder.get_embedding_dimension()

        assert dimension == 768


# ============================================================================
# LLM Operations Tests (10 tests)
# ============================================================================


class TestLLMOperations:
    """Test LLM prompt and generation operations."""

    @pytest.fixture
    def llm_prompt(self, vertex_client, mock_generative_model):
        """Provide an LLM prompt handler."""
        return LLMPrompt()

    def test_generate_text_success(self, llm_prompt):
        """
        Given: Valid prompt text
        When: Generating text
        Then: Response text is returned
        """
        prompt = "What is the capital of France?"

        result = llm_prompt.generate(prompt)

        assert isinstance(result, str)
        assert "Response to:" in result

    def test_generate_with_system_instruction(self, llm_prompt):
        """
        Given: Prompt with system instruction
        When: Generating text
        Then: System instruction is used
        """
        prompt = "Hello"
        system = "You are a helpful assistant"

        result = llm_prompt.generate(prompt, system_instruction=system)

        assert isinstance(result, str)

    def test_generate_with_examples(self, llm_prompt):
        """
        Given: Prompt with few-shot examples
        When: Generating text
        Then: Examples are included in context
        """
        prompt = "Translate to French"
        examples = [
            ("Hello", "Bonjour"),
            ("Goodbye", "Au revoir"),
        ]

        result = llm_prompt.generate(prompt, examples=examples)

        assert isinstance(result, str)

    def test_generate_with_custom_temperature(self, llm_prompt):
        """
        Given: Custom temperature parameter
        When: Generating text
        Then: Temperature is applied
        """
        result = llm_prompt.generate("Test", temperature=0.3)

        assert isinstance(result, str)

    def test_generate_retry_on_failure(self, vertex_client):
        """
        Given: Model that fails once
        When: Generating text with retry
        Then: Successfully retries and returns result
        """
        with patch("atoms_mcp.adapters.secondary.vertex.llm.GenerativeModel") as mock:
            model = MockGenerativeModel(should_fail=True, failure_count=1)
            mock.return_value = model

            with patch("atoms_mcp.adapters.secondary.vertex.llm.time.sleep"):
                llm = LLMPrompt()
                result = llm.generate("test")

                assert isinstance(result, str)
                assert model.call_count == 2

    def test_generate_max_retries_exceeded(self, vertex_client):
        """
        Given: Model that always fails
        When: Generating text
        Then: LLMError is raised after max retries
        """
        with patch("atoms_mcp.adapters.secondary.vertex.llm.GenerativeModel") as mock:
            model = MockGenerativeModel(should_fail=True, failure_count=10)
            mock.return_value = model

            with patch("atoms_mcp.adapters.secondary.vertex.llm.time.sleep"):
                llm = LLMPrompt()

                with pytest.raises(LLMError, match="after 3 attempts"):
                    llm.generate("test")

    def test_generate_stream_success(self, llm_prompt):
        """
        Given: Valid prompt text
        When: Generating streaming response
        Then: Text chunks are yielded
        """
        prompt = "Stream this response"

        chunks = list(llm_prompt.generate_stream(prompt))

        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_generate_stream_with_examples(self, llm_prompt):
        """
        Given: Streaming with few-shot examples
        When: Generating stream
        Then: Examples are used in context
        """
        prompt = "Continue"
        examples = [("Start", "Begin")]

        chunks = list(llm_prompt.generate_stream(prompt, examples=examples))

        assert len(chunks) > 0

    def test_count_tokens(self, llm_prompt):
        """
        Given: Text to count
        When: Counting tokens
        Then: Token count is returned
        """
        text = "This is a test sentence with multiple words"

        count = llm_prompt.count_tokens(text)

        assert isinstance(count, int)
        assert count > 0

    def test_estimate_cost(self, llm_prompt):
        """
        Given: Token counts
        When: Estimating cost
        Then: Cost is calculated
        """
        cost = llm_prompt.estimate_cost(
            input_tokens=1000,
            output_tokens=500,
        )

        assert isinstance(cost, float)
        assert cost > 0


# ============================================================================
# Conversation Management Tests (5 tests)
# ============================================================================


class TestConversationManagement:
    """Test conversation manager for multi-turn interactions."""

    @pytest.fixture
    def conversation(self, vertex_client, mock_generative_model):
        """Provide a conversation manager."""
        llm = LLMPrompt()
        return ConversationManager(llm)

    def test_send_message_single_turn(self, conversation):
        """
        Given: New conversation
        When: Sending first message
        Then: Response is returned and history is updated
        """
        response = conversation.send_message("Hello")

        assert isinstance(response, str)
        assert len(conversation.get_history()) == 1

    def test_send_message_multi_turn(self, conversation):
        """
        Given: Ongoing conversation
        When: Sending multiple messages
        Then: All turns are tracked in history
        """
        conversation.send_message("First message")
        conversation.send_message("Second message")
        conversation.send_message("Third message")

        history = conversation.get_history()
        assert len(history) == 3

    def test_conversation_history_limit(self, vertex_client, mock_generative_model):
        """
        Given: Conversation with max_history limit
        When: Exceeding the limit
        Then: Old messages are removed
        """
        llm = LLMPrompt()
        conversation = ConversationManager(llm, max_history=3)

        for i in range(5):
            conversation.send_message(f"Message {i}")

        history = conversation.get_history()
        assert len(history) == 3
        # Should keep last 3 messages
        assert history[0][0] == "Message 2"

    def test_clear_history(self, conversation):
        """
        Given: Conversation with history
        When: Clearing history
        Then: History is emptied
        """
        conversation.send_message("Message 1")
        conversation.send_message("Message 2")

        assert len(conversation.get_history()) == 2

        conversation.clear_history()

        assert len(conversation.get_history()) == 0

    def test_conversation_with_system_instruction(self, vertex_client, mock_generative_model):
        """
        Given: Conversation with system instruction
        When: Sending messages
        Then: System instruction is used for all messages
        """
        llm = LLMPrompt()
        system = "You are a math tutor"
        conversation = ConversationManager(llm, system_instruction=system)

        response = conversation.send_message("What is 2+2?")

        assert isinstance(response, str)


# ============================================================================
# Error Handling and Edge Cases (5 tests)
# ============================================================================


class TestVertexAIErrorHandling:
    """Test error handling in Vertex AI adapter."""

    def test_embedding_model_load_error(self, vertex_client):
        """
        Given: Invalid model name
        When: Attempting to load model
        Then: EmbeddingError is raised
        """
        with patch("atoms_mcp.adapters.secondary.vertex.embeddings.TextEmbeddingModel") as mock:
            mock.from_pretrained.side_effect = Exception("Model not found")

            embedder = TextEmbedder()

            with pytest.raises(EmbeddingError, match="Failed to load embedding model"):
                embedder.generate_embedding("test")

    def test_llm_model_load_error(self, vertex_client):
        """
        Given: Invalid model configuration
        When: Attempting to generate text
        Then: LLMError is raised
        """
        with patch("atoms_mcp.adapters.secondary.vertex.llm.GenerativeModel") as mock:
            mock.side_effect = Exception("Model initialization failed")

            llm = LLMPrompt()

            with pytest.raises(LLMError, match="Failed to load model"):
                llm.generate("test")

    def test_embedding_empty_response(self, vertex_client):
        """
        Given: Model returns no embeddings
        When: Generating embedding
        Then: EmbeddingError is raised
        """
        with patch("atoms_mcp.adapters.secondary.vertex.embeddings.TextEmbeddingModel") as mock:
            model = MagicMock()
            model.get_embeddings.return_value = []
            mock.from_pretrained.return_value = model

            embedder = TextEmbedder()

            with pytest.raises(EmbeddingError, match="returned no embeddings"):
                embedder.generate_embedding("test")

    def test_llm_empty_response(self, vertex_client):
        """
        Given: Model returns empty text
        When: Generating text
        Then: LLMError is raised
        """
        with patch("atoms_mcp.adapters.secondary.vertex.llm.GenerativeModel") as mock:
            model = MagicMock()
            response = MagicMock()
            response.text = ""
            model.generate_content.return_value = response
            mock.return_value = model

            llm = LLMPrompt()

            with pytest.raises(LLMError, match="empty response"):
                llm.generate("test")

    def test_rate_limit_handling(self, vertex_client):
        """
        Given: API rate limit exceeded
        When: Making requests
        Then: Automatic retry with backoff
        """
        with patch("atoms_mcp.adapters.secondary.vertex.embeddings.TextEmbeddingModel") as mock:
            from google.api_core.exceptions import ResourceExhausted

            model = MagicMock()
            # Fail twice with rate limit, then succeed
            model.get_embeddings.side_effect = [
                ResourceExhausted("Rate limit"),
                ResourceExhausted("Rate limit"),
                [MockEmbedding([0.1] * 768)],
            ]
            mock.from_pretrained.return_value = model

            with patch("atoms_mcp.adapters.secondary.vertex.embeddings.time.sleep"):
                embedder = TextEmbedder()
                result = embedder.generate_embedding("test")

                assert isinstance(result, list)
                assert model.get_embeddings.call_count == 3
