import json
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

import httpx

from schema import (
    ChatHistory,
    ChatHistoryInput,
    ChatMessage,
    Feedback,
    FeedbackResponse,
    ServiceMetadata,
    StreamInput,
    UserInput,
    UserThreads,
    UserThreadsInput,
)


class AgentClientError(Exception):
    pass


class AgentClient:
    """Client for interacting with the agent service."""

    def __init__(
        self,
        base_url: str | None = None,
        agent: str | None = None,
        timeout: float | None = None,
        get_info: bool = True,
    ) -> None:
        """
        Initialize the client.

        Args:
            base_url (str, optional): The base URL of the agent service.
                Defaults to AGENT_SERVICE_URL environment variable or "http://0.0.0.0:7860".
            agent (str, optional): The name of the default agent to use.
            timeout (float, optional): The timeout for requests in seconds.
            get_info (bool, optional): Whether to fetch agent information on init.
                Default: True
        """
        self.base_url = (
            base_url
            or os.getenv("AGENT_SERVICE_URL")
            or os.getenv("BASE_URL")
            or "http://0.0.0.0:7860"
        ).rstrip("/")
        self.auth_secret = os.getenv("AUTH_SECRET")
        self.timeout = timeout
        self.info: ServiceMetadata | None = None
        self.agent: str | None = None
        if get_info:
            self.retrieve_info()
        if agent:
            self.update_agent(agent)

    @property
    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.auth_secret:
            headers["Authorization"] = f"Bearer {self.auth_secret}"
        return headers

    def retrieve_info(self) -> None:
        try:
            response = httpx.get(
                f"{self.base_url}/info",
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise AgentClientError(f"Error getting service info: {e}") from e

        self.info = ServiceMetadata.model_validate(response.json())
        if not self.agent or self.agent not in [a.key for a in self.info.agents]:
            self.agent = self.info.default_agent

    def update_agent(self, agent: str, verify: bool = True) -> None:
        if verify:
            if not self.info:
                self.retrieve_info()
            agent_keys = [a.key for a in self.info.agents]  # type: ignore[union-attr]
            if agent not in agent_keys:
                raise AgentClientError(
                    f"Agent {agent} not found in available agents: {', '.join(agent_keys)}"
                )
        self.agent = agent

    async def ainvoke(
        self,
        message: str,
        model: str | None = None,
        thread_id: str | None = None,
        user_id: str | None = None,
        agent_config: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """
        Invoke the agent asynchronously. Only the final message is returned.

        Args:
            message (str): The message to send to the agent
            model (str, optional): LLM model to use for the agent
            thread_id (str, optional): Thread ID for continuing a conversation
            user_id (str, optional): User ID for continuing a conversation across multiple threads
            agent_config (dict[str, Any], optional): Additional configuration to pass through to the agent

        Returns:
            ChatMessage: The response from the agent
        """
        if not self.agent:
            raise AgentClientError("No agent selected. Use update_agent() to select an agent.")
        request = UserInput(message=message)
        if thread_id:
            request.thread_id = thread_id
        if model:
            request.model = model  # type: ignore[assignment]
        if agent_config:
            request.agent_config = agent_config
        if user_id:
            request.user_id = user_id
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{self.agent}/invoke",
                    json=request.model_dump(),
                    headers=self._headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise AgentClientError(f"Error: {e}") from e

        return ChatMessage.model_validate(response.json())

    def invoke(
        self,
        message: str,
        model: str | None = None,
        thread_id: str | None = None,
        user_id: str | None = None,
        agent_config: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """
        Invoke the agent synchronously. Only the final message is returned.

        Args:
            message (str): The message to send to the agent
            model (str, optional): LLM model to use for the agent
            thread_id (str, optional): Thread ID for continuing a conversation
            user_id (str, optional): User ID for continuing a conversation across multiple threads
            agent_config (dict[str, Any], optional): Additional configuration to pass through to the agent

        Returns:
            ChatMessage: The response from the agent
        """
        if not self.agent:
            raise AgentClientError("No agent selected. Use update_agent() to select an agent.")
        request = UserInput(message=message)
        if thread_id:
            request.thread_id = thread_id
        if model:
            request.model = model  # type: ignore[assignment]
        if agent_config:
            request.agent_config = agent_config
        if user_id:
            request.user_id = user_id
        try:
            response = httpx.post(
                f"{self.base_url}/{self.agent}/invoke",
                json=request.model_dump(),
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise AgentClientError(f"Error: {e}") from e

        return ChatMessage.model_validate(response.json())

    def _parse_stream_line(self, line: str) -> ChatMessage | str | None:
        line = line.strip()
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                return None
            try:
                parsed = json.loads(data)
            except Exception as e:
                raise Exception(f"Error JSON parsing message from server: {e}") from e
            match parsed.get("type"):
                case "message":
                    try:
                        return ChatMessage.model_validate(parsed["content"])
                    except Exception as e:
                        raise Exception(f"Server returned invalid message: {e}") from e
                case "token":
                    return parsed["content"]
                case "error":
                    error_msg = "Error: " + parsed.get("content", "Unknown error")
                    return ChatMessage(type="ai", content=error_msg)
        return None

    def stream(
        self,
        message: str,
        model: str | None = None,
        thread_id: str | None = None,
        user_id: str | None = None,
        agent_config: dict[str, Any] | None = None,
        stream_tokens: bool = True,
    ) -> Generator[ChatMessage | str, None, None]:
        """
        Stream the agent's response synchronously.

        Each intermediate message of the agent process is yielded as a ChatMessage.
        If stream_tokens is True (the default value), the response will also yield
        content tokens from streaming models as they are generated.

        Args:
            message (str): The message to send to the agent
            model (str, optional): LLM model to use for the agent
            thread_id (str, optional): Thread ID for continuing a conversation
            user_id (str, optional): User ID for continuing a conversation across multiple threads
            agent_config (dict[str, Any], optional): Additional configuration to pass through to the agent
            stream_tokens (bool, optional): Stream tokens as they are generated. Default: True

        Returns:
            Generator[ChatMessage | str, None, None]: The response from the agent
        """
        if not self.agent:
            raise AgentClientError("No agent selected. Use update_agent() to select an agent.")
        request = StreamInput(message=message, stream_tokens=stream_tokens)
        if thread_id:
            request.thread_id = thread_id
        if user_id:
            request.user_id = user_id
        if model:
            request.model = model  # type: ignore[assignment]
        if agent_config:
            request.agent_config = agent_config
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/{self.agent}/stream",
                json=request.model_dump(),
                headers=self._headers,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip():
                        parsed = self._parse_stream_line(line)
                        if parsed is None:
                            break
                        yield parsed
        except httpx.HTTPError as e:
            raise AgentClientError(f"Error: {e}") from e

    async def astream(
        self,
        message: str,
        model: str | None = None,
        thread_id: str | None = None,
        user_id: str | None = None,
        agent_config: dict[str, Any] | None = None,
        stream_tokens: bool = True,
    ) -> AsyncGenerator[ChatMessage | str, None]:
        """
        Stream the agent's response asynchronously.

        Each intermediate message of the agent process is yielded as a ChatMessage.
        If stream_tokens is True (the default value), the response will also yield
        content tokens from streaming models as they are generated.

        Args:
            message (str): The message to send to the agent
            model (str, optional): LLM model to use for the agent
            thread_id (str, optional): Thread ID for continuing a conversation
            user_id (str, optional): User ID for continuing a conversation across multiple threads
            agent_config (dict[str, Any], optional): Additional configuration to pass through to the agent
            stream_tokens (bool, optional): Stream tokens as they are generated. Default: True

        Returns:
            AsyncGenerator[ChatMessage | str, None]: The response from the agent
        """
        if not self.agent:
            raise AgentClientError("No agent selected. Use update_agent() to select an agent.")
        request = StreamInput(message=message, stream_tokens=stream_tokens)
        if thread_id:
            request.thread_id = thread_id
        if model:
            request.model = model  # type: ignore[assignment]
        if agent_config:
            request.agent_config = agent_config
        if user_id:
            request.user_id = user_id
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/{self.agent}/stream",
                    json=request.model_dump(),
                    headers=self._headers,
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            parsed = self._parse_stream_line(line)
                            if parsed is None:
                                break
                            if parsed != "":
                                yield parsed
            except httpx.HTTPError as e:
                raise AgentClientError(f"Error: {e}") from e

    async def acreate_feedback(
        self, run_id: str, key: str, score: float, kwargs: dict[str, Any] | None = None
    ) -> FeedbackResponse:
        """
        Create a feedback record for a run asynchronously.

        This is a simple wrapper for the LangSmith create_feedback API, so credentials
        can be stored and managed in the service rather than the client.
        """
        request = Feedback(run_id=run_id, key=key, score=score, kwargs=kwargs or {})
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/feedback",
                    json=request.model_dump(),
                    headers=self._headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return FeedbackResponse.model_validate(response.json())
            except httpx.HTTPError as e:
                raise AgentClientError(f"Error submitting feedback: {e}") from e

    def create_feedback(
        self, run_id: str, key: str, score: float, kwargs: dict[str, Any] | None = None
    ) -> FeedbackResponse:
        """
        Create a feedback record for a run synchronously.
        """
        request = Feedback(run_id=run_id, key=key, score=score, kwargs=kwargs or {})
        try:
            response = httpx.post(
                f"{self.base_url}/feedback",
                json=request.model_dump(),
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return FeedbackResponse.model_validate(response.json())
        except httpx.HTTPError as e:
            raise AgentClientError(f"Error submitting feedback: {e}") from e

    def feedback(
        self, run_id: str, key: str, score: float, kwargs: dict[str, Any] | None = None
    ) -> FeedbackResponse:
        """Convenience alias for create_feedback."""
        return self.create_feedback(run_id=run_id, key=key, score=score, kwargs=kwargs)

    def get_history(
        self,
        thread_id: str,
        user_id: str | None = None,
        agent: str | None = None,
    ) -> ChatHistory:
        """
        Get chat history for a thread synchronously.

        Args:
            thread_id (str): Thread ID for identifying a conversation
            user_id (str, optional): User ID to scope history
            agent (str, optional): The agent whose graph interprets the thread
        """
        agent = agent or self.agent
        request = ChatHistoryInput(thread_id=thread_id, user_id=user_id)
        url = f"{self.base_url}/{agent}/history" if agent else f"{self.base_url}/history"
        try:
            response = httpx.post(
                url,
                json=request.model_dump(),
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return ChatHistory.model_validate(data)
        except httpx.HTTPError as e:
            raise AgentClientError(f"Error retrieving history: {e}") from e

    async def aget_history(
        self,
        thread_id: str,
        user_id: str | None = None,
        agent: str | None = None,
    ) -> ChatHistory:
        """
        Get chat history for a thread asynchronously.
        """
        agent = agent or self.agent
        request = ChatHistoryInput(thread_id=thread_id, user_id=user_id)
        url = f"{self.base_url}/{agent}/history" if agent else f"{self.base_url}/history"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=request.model_dump(),
                    headers=self._headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                return ChatHistory.model_validate(data)
            except httpx.HTTPError as e:
                raise AgentClientError(f"Error retrieving history: {e}") from e

    def _user_threads_request(
        self, user_id: str, agent: str | None, limit: int
    ) -> tuple[str, dict[str, Any]]:
        agent_id = agent or self.agent
        url = (
            f"{self.base_url}/{agent_id}/threads"
            if agent_id
            else f"{self.base_url}/history/threads"
        )
        return url, UserThreadsInput(user_id=user_id, limit=limit).model_dump()

    def get_user_threads(
        self, user_id: str, agent: str | None = None, limit: int = 20
    ) -> UserThreads:
        """
        List a user's conversation threads synchronously.

        Args:
            user_id (str): User ID to list threads for.
            agent (str, optional): The agent whose threads should be listed.
            limit (int, optional): Maximum number of threads to return.
        """
        url, payload = self._user_threads_request(user_id, agent, limit)
        try:
            # Fallback handling: try GET first, or POST to /history/threads
            if url.endswith("/history/threads"):
                response = httpx.post(
                    url,
                    json=payload,
                    headers=self._headers,
                    timeout=self.timeout,
                )
            else:
                response = httpx.get(
                    url,
                    params=payload,
                    headers=self._headers,
                    timeout=self.timeout,
                )
            response.raise_for_status()
            return UserThreads.model_validate(response.json())
        except httpx.HTTPError as e:
            raise AgentClientError(f"Error listing user threads: {e}") from e

    async def aget_user_threads(
        self, user_id: str, agent: str | None = None, limit: int = 20
    ) -> UserThreads:
        """
        List a user's conversation threads asynchronously.

        Args:
            user_id (str): User ID to list threads for.
            agent (str, optional): The agent whose threads should be listed.
            limit (int, optional): Maximum number of threads to return.
        """
        url, payload = self._user_threads_request(user_id, agent, limit)
        async with httpx.AsyncClient() as client:
            try:
                if url.endswith("/history/threads"):
                    response = await client.post(
                        url,
                        json=payload,
                        headers=self._headers,
                        timeout=self.timeout,
                    )
                else:
                    response = await client.get(
                        url,
                        params=payload,
                        headers=self._headers,
                        timeout=self.timeout,
                    )
                response.raise_for_status()
                return UserThreads.model_validate(response.json())
            except httpx.HTTPError as e:
                raise AgentClientError(f"Error listing user threads: {e}") from e

    def list_threads(self, user_id: str, agent: str | None = None, limit: int = 20) -> UserThreads:
        """Convenience alias for get_user_threads."""
        return self.get_user_threads(user_id=user_id, agent=agent, limit=limit)

    async def alist_threads(
        self, user_id: str, agent: str | None = None, limit: int = 20
    ) -> UserThreads:
        """Convenience alias for aget_user_threads."""
        return await self.aget_user_threads(user_id=user_id, agent=agent, limit=limit)
