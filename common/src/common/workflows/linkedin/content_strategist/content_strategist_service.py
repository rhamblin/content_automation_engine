from pathlib import Path

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FileSearchTool, FilePurpose, ListSortOrder
from azure.identity import DefaultAzureCredential
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common.app_logger import AppLogger
from common.workflows.linkedin.content_strategist.content_strategist_request import (
    ContentStrategistConfig,
)
from common.workflows.linkedin.content_strategist.content_strategist_response import (
    ChatResponse,
)

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".doc", ".md", ".json", ".csv"}


class ContentStrategistService:
    """Interactive chat agent with RAG grounding via Azure Foundry Agents.

    Lifecycle:
        1. initialize() — upload files, create vector store, agent, thread
        2. chat(message) — send user message, get agent response
        3. cleanup()   — delete agent, vector store, files, thread
    """

    def __init__(self, config: ContentStrategistConfig) -> None:
        self.config = config
        self.logger = AppLogger(__name__)

        self._client: AgentsClient | None = None
        self._agent_id: str | None = None
        self._thread_id: str | None = None
        self._vector_store_id: str | None = None
        self._uploaded_file_ids: list[str] = []

    def initialize(self) -> None:
        """Set up the Foundry agent with file search grounding."""
        self.logger.info("Initializing content strategist agent...")

        self._client = AgentsClient(
            endpoint=self.config.project_endpoint,
            credential=DefaultAzureCredential(),
        )

        self._upload_grounding_files()
        self._create_vector_store()
        self._create_agent()
        self._create_thread()

        self.logger.info("Content strategist ready.")

    def chat(self, user_message: str) -> ChatResponse:
        """Send a message and return the agent's response."""
        if not self._client or not self._thread_id or not self._agent_id:
            raise RuntimeError("Service not initialized. Call initialize() first.")

        self._client.messages.create(
            thread_id=self._thread_id,
            role="user",
            content=user_message,
        )

        run = self._run_agent()
        return self._extract_response(run)

    def cleanup(self) -> None:
        """Delete all Azure resources created during the session."""
        if not self._client:
            return

        self.logger.info("Cleaning up agent resources...")

        try:
            if self._thread_id:
                self._client.threads.delete(self._thread_id)
                self.logger.info("Deleted thread.")
        except Exception as e:
            self.logger.warning(f"Failed to delete thread: {e}")

        try:
            if self._agent_id:
                self._client.delete_agent(self._agent_id)
                self.logger.info("Deleted agent.")
        except Exception as e:
            self.logger.warning(f"Failed to delete agent: {e}")

        try:
            if self._vector_store_id:
                self._client.vector_stores.delete(self._vector_store_id)
                self.logger.info("Deleted vector store.")
        except Exception as e:
            self.logger.warning(f"Failed to delete vector store: {e}")

        for file_id in self._uploaded_file_ids:
            try:
                self._client.files.delete(file_id=file_id)
            except Exception as e:
                self.logger.warning(f"Failed to delete file {file_id}: {e}")

        if self._uploaded_file_ids:
            self.logger.info(
                f"Deleted {len(self._uploaded_file_ids)} uploaded files."
            )

        self._agent_id = None
        self._thread_id = None
        self._vector_store_id = None
        self._uploaded_file_ids = []

    def _upload_grounding_files(self) -> None:
        """Upload all supported files from the grounding directory."""
        grounding_dir = self.config.grounding_dir
        if not grounding_dir.exists():
            self.logger.warning(
                f"Grounding directory does not exist: {grounding_dir}"
            )
            return

        files = [
            f
            for f in grounding_dir.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not files:
            self.logger.warning(f"No grounding files found in {grounding_dir}")
            return

        for file_path in files:
            uploaded = self._upload_single_file(file_path)
            if uploaded:
                self._uploaded_file_ids.append(uploaded)

        self.logger.info(
            f"Uploaded {len(self._uploaded_file_ids)} grounding files."
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ConnectionError),
        reraise=True,
    )
    def _upload_single_file(self, file_path: Path) -> str | None:
        """Upload a single file to Azure Foundry. Returns file ID or None."""
        try:
            uploaded = self._client.files.upload_and_poll(
                file_path=str(file_path),
                purpose=FilePurpose.AGENTS,
            )
            self.logger.info(f"Uploaded: {file_path.name} -> {uploaded.id}")
            return uploaded.id
        except Exception as e:
            self.logger.error(f"Failed to upload {file_path.name}: {e}")
            return None

    def _create_vector_store(self) -> None:
        """Create a vector store with all uploaded files."""
        if not self._uploaded_file_ids:
            self.logger.info("No files uploaded — skipping vector store creation.")
            return

        vector_store = self._client.vector_stores.create_and_poll(
            file_ids=self._uploaded_file_ids,
            name="linkedin-strategist-grounding",
        )
        self._vector_store_id = vector_store.id
        self.logger.info(f"Created vector store: {vector_store.id}")

    def _create_agent(self) -> None:
        """Create the Foundry agent with file search tool."""
        kwargs = {}

        if self._vector_store_id:
            file_search = FileSearchTool(
                vector_store_ids=[self._vector_store_id]
            )
            kwargs["tools"] = file_search.definitions
            kwargs["tool_resources"] = file_search.resources

        agent = self._client.create_agent(
            model=self.config.model,
            name="linkedin-content-strategist",
            instructions=self.config.persona_prompt,
            **kwargs,
        )
        self._agent_id = agent.id
        self.logger.info(f"Created agent: {agent.id}")

    def _create_thread(self) -> None:
        """Create a conversation thread."""
        thread = self._client.threads.create()
        self._thread_id = thread.id
        self.logger.info(f"Created thread: {thread.id}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ConnectionError),
        reraise=True,
    )
    def _run_agent(self):
        """Execute a run on the current thread and wait for completion."""
        try:
            run = self._client.runs.create_and_process(
                thread_id=self._thread_id,
                agent_id=self._agent_id,
            )
            return run
        except Exception as e:
            raise ConnectionError(f"Agent run failed: {e}") from e

    def _extract_response(self, run) -> ChatResponse:
        """Extract the agent's text response from the completed run."""
        messages = self._client.messages.list(
            thread_id=self._thread_id,
            order=ListSortOrder.DESCENDING,
        )

        response_text = ""
        annotations: list[str] = []

        for msg in messages:
            if msg.role == "assistant":
                if msg.text_messages:
                    response_text = msg.text_messages[-1].text.value

                if hasattr(msg, "file_citation_annotations") and msg.file_citation_annotations:
                    for ann in msg.file_citation_annotations:
                        annotations.append(ann.text)
                break

        return ChatResponse(message=response_text, annotations=annotations)
