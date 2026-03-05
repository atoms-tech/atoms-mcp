"""
Vertex AI LLM interface for text generation.

This module provides LLM prompting capabilities using Google Vertex AI
with support for system prompts, few-shot examples, streaming, and
token counting.
"""

from __future__ import annotations

import time
from typing import Any, Generator, Optional

from google.api_core import exceptions as google_exceptions
from vertexai.generative_models import (
    Content,
    GenerationConfig,
    GenerativeModel,
    Part,
)

from atoms_mcp.adapters.secondary.vertex.client import get_client, VertexAIClientError


class LLMError(Exception):
    """Exception raised for LLM operation errors."""

    pass


class LLMPrompt:
    """
    Manages LLM prompting with Vertex AI Gemini models.

    This class provides:
    - Prompt generation with system instructions
    - Few-shot example support
    - Streaming and non-streaming responses
    - Token counting
    - Error handling with retry logic
    """

    def __init__(
        self,
        model_name: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40,
    ) -> None:
        """
        Initialize LLM prompt handler.

        Args:
            model_name: Gemini model name
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
        """
        self.client = get_client()
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.top_p = top_p
        self.top_k = top_k

    def _get_model(
        self,
        system_instruction: Optional[str] = None,
    ) -> GenerativeModel:
        """
        Get configured generative model.

        Args:
            system_instruction: Optional system prompt

        Returns:
            GenerativeModel: Configured model

        Raises:
            LLMError: If model loading fails
        """
        try:
            return GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
            )
        except Exception as e:
            raise LLMError(f"Failed to load model {self.model_name}: {e}") from e

    def _get_generation_config(
        self,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> GenerationConfig:
        """
        Get generation configuration.

        Args:
            temperature: Override default temperature
            max_output_tokens: Override default max tokens
            top_p: Override default top_p
            top_k: Override default top_k

        Returns:
            GenerationConfig: Configuration object
        """
        return GenerationConfig(
            temperature=temperature or self.temperature,
            max_output_tokens=max_output_tokens or self.max_output_tokens,
            top_p=top_p or self.top_p,
            top_k=top_k or self.top_k,
        )

    def _format_examples(
        self,
        examples: list[tuple[str, str]],
    ) -> list[Content]:
        """
        Format few-shot examples as conversation history.

        Args:
            examples: List of (user_message, model_response) tuples

        Returns:
            List of Content objects for conversation history
        """
        history = []
        for user_msg, model_msg in examples:
            history.append(Content(role="user", parts=[Part.from_text(user_msg)]))
            history.append(Content(role="model", parts=[Part.from_text(model_msg)]))
        return history

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        examples: Optional[list[tuple[str, str]]] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text response from prompt.

        Args:
            prompt: User prompt text
            system_instruction: Optional system instruction
            examples: Optional few-shot examples as (user, assistant) tuples
            temperature: Override temperature
            max_output_tokens: Override max output tokens

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails
        """
        try:
            model = self._get_model(system_instruction=system_instruction)
            config = self._get_generation_config(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

            # Format history with examples
            history = self._format_examples(examples) if examples else None

            # Generate with retry
            for attempt in range(self.client.max_retries):
                try:
                    if history:
                        # Start chat with history
                        chat = model.start_chat(history=history)
                        response = chat.send_message(prompt, generation_config=config)
                    else:
                        # Simple generation
                        response = model.generate_content(prompt, generation_config=config)

                    if response and response.text:
                        return response.text

                    raise LLMError("Model returned empty response")

                except google_exceptions.GoogleAPIError as e:
                    if attempt < self.client.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise LLMError(f"API error after {attempt + 1} attempts: {e}") from e

            raise LLMError(f"Failed after {self.client.max_retries} attempts")

        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMError(f"Failed to generate response: {e}") from e

    def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        examples: Optional[list[tuple[str, str]]] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """
        Generate streaming text response from prompt.

        Args:
            prompt: User prompt text
            system_instruction: Optional system instruction
            examples: Optional few-shot examples as (user, assistant) tuples
            temperature: Override temperature
            max_output_tokens: Override max output tokens

        Yields:
            Text chunks as they are generated

        Raises:
            LLMError: If generation fails
        """
        try:
            model = self._get_model(system_instruction=system_instruction)
            config = self._get_generation_config(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

            # Format history with examples
            history = self._format_examples(examples) if examples else None

            # Generate with retry
            for attempt in range(self.client.max_retries):
                try:
                    if history:
                        # Start chat with history
                        chat = model.start_chat(history=history)
                        response_stream = chat.send_message(
                            prompt,
                            generation_config=config,
                            stream=True,
                        )
                    else:
                        # Simple streaming generation
                        response_stream = model.generate_content(
                            prompt,
                            generation_config=config,
                            stream=True,
                        )

                    # Yield chunks as they arrive
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text

                    return  # Success, exit retry loop

                except google_exceptions.GoogleAPIError as e:
                    if attempt < self.client.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise LLMError(f"API error after {attempt + 1} attempts: {e}") from e

            raise LLMError(f"Failed after {self.client.max_retries} attempts")

        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMError(f"Failed to generate streaming response: {e}") from e

    def count_tokens(
        self,
        text: str,
        system_instruction: Optional[str] = None,
    ) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for
            system_instruction: Optional system instruction to include

        Returns:
            Number of tokens

        Raises:
            LLMError: If token counting fails
        """
        try:
            model = self._get_model(system_instruction=system_instruction)

            # Count tokens
            response = model.count_tokens(text)

            return response.total_tokens

        except Exception as e:
            raise LLMError(f"Failed to count tokens: {e}") from e

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        input_cost_per_1k: float = 0.00025,
        output_cost_per_1k: float = 0.0005,
    ) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            input_cost_per_1k: Cost per 1000 input tokens (default for Gemini 1.5 Pro)
            output_cost_per_1k: Cost per 1000 output tokens

        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        return input_cost + output_cost


class ConversationManager:
    """
    Manages multi-turn conversations with context.

    This class maintains conversation history and provides
    convenient methods for multi-turn interactions.
    """

    def __init__(
        self,
        llm: LLMPrompt,
        system_instruction: Optional[str] = None,
        max_history: int = 20,
    ) -> None:
        """
        Initialize conversation manager.

        Args:
            llm: LLM prompt handler
            system_instruction: Optional system instruction for all messages
            max_history: Maximum number of turns to keep in history
        """
        self.llm = llm
        self.system_instruction = system_instruction
        self.max_history = max_history
        self.history: list[tuple[str, str]] = []

    def send_message(
        self,
        message: str,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a message in the conversation.

        Args:
            message: User message
            temperature: Override temperature

        Returns:
            Assistant response

        Raises:
            LLMError: If generation fails
        """
        # Generate response with full history
        response = self.llm.generate(
            prompt=message,
            system_instruction=self.system_instruction,
            examples=self.history,
            temperature=temperature,
        )

        # Add to history
        self.history.append((message, response))

        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

        return response

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history.clear()

    def get_history(self) -> list[tuple[str, str]]:
        """
        Get conversation history.

        Returns:
            List of (user_message, assistant_response) tuples
        """
        return self.history.copy()
