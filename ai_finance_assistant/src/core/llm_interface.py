import os
import logging
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

logger = logging.getLogger(__name__)


class LangfuseAdapter:
    """Optional adapter that forwards prompts/responses to Langfuse if available.

    Implementation is intentionally defensive: it only attempts to import and initialize
    Langfuse when a supported key is provided. It supports both modern SDK keys
    (`LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`) and legacy `LANGFUSE_API_KEY`.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        public_key: Optional[str] = None,
        host: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.client = None
        self.api_key = api_key
        self.secret_key = secret_key
        self.public_key = public_key
        self.host = host
        self.base_url = base_url
        self.project = os.environ.get("LANGFUSE_PROJECT")
        self.environment = os.environ.get("LANGFUSE_ENV")
        self.debug_mode = os.environ.get("LANGFUSE_DEBUG", "false").lower() in ("1", "true", "yes")

        logger.info(
            "LangfuseAdapter init: secret_key_set=%s public_key_set=%s api_key_set=%s host=%s base_url=%s project=%s environment=%s debug=%s",
            bool(secret_key),
            bool(public_key),
            bool(api_key),
            host,
            base_url,
            self.project,
            self.environment,
            self.debug_mode,
        )

        if not any((api_key, secret_key, public_key)):
            logger.warning(
                "No Langfuse credentials provided; set LANGFUSE_SECRET_KEY/LANGFUSE_PUBLIC_KEY or legacy LANGFUSE_API_KEY"
            )
            return

        if api_key and not (secret_key or public_key):
            secret_key = api_key
            public_key = api_key

        try:
            import langfuse as lf  # type: ignore
        except Exception as e:
            logger.warning("Langfuse SDK not available: %s", e)
            return

        client_kwargs = {}
        if public_key:
            client_kwargs["public_key"] = public_key
        if secret_key:
            client_kwargs["secret_key"] = secret_key
        if host:
            client_kwargs["host"] = host
        elif base_url:
            client_kwargs["base_url"] = base_url
        if self.environment:
            client_kwargs["environment"] = self.environment
        if self.debug_mode:
            client_kwargs["debug"] = True

        try:
            self.client = lf.Langfuse(**client_kwargs)
            logger.info(
                "Langfuse client initialized with %s",
                ", ".join(sorted(client_kwargs.keys())),
            )
        except Exception as e:
            logger.warning("Langfuse client initialization failed: %s", e)

        if self.client:
            logger.info("Langfuse client initialized")
        else:
            logger.warning("Langfuse client could not be initialized")

    def _build_payload(self, prompt: str, response: str, model: str, token_usage: Optional[dict] = None, metadata: Optional[dict] = None) -> dict:
        payload = {
            "event": "llm_generation",
            "prompt": prompt,
            "response": response,
            "model": model,
            "token_usage": token_usage or {},
            "metadata": metadata or {},
        }
        if self.project:
            payload["project"] = self.project
        if self.environment:
            payload["environment"] = self.environment
        return payload

    def start_generation(self, name: str, prompt: str, model: str, metadata: Optional[dict] = None, model_parameters: Optional[dict] = None, completion_start_time: Optional[datetime] = None):
        if not self.client:
            return nullcontext(None)
        try:
            return self.client.start_as_current_observation(
                name=name,
                as_type="generation",
                input=prompt,
                model=model,
                model_parameters=model_parameters,
                metadata=metadata or {},
                completion_start_time=completion_start_time,
            )
        except Exception as e:
            logger.warning("Langfuse start_generation failed: %s", e)
            return nullcontext(None)

    def update_generation(self, generation, output: str, token_usage: Optional[dict] = None, metadata: Optional[dict] = None):
        if generation is None:
            return
        try:
            generation.update(
                output=output,
                usage_details=token_usage or {},
                metadata=metadata or {},
            )
        except Exception:
            logger.exception("Langfuse update_generation failed")

    def get_trace_url(self, trace_id: Optional[str] = None) -> Optional[str]:
        if not self.client:
            return None
        try:
            return self.client.get_trace_url(trace_id=trace_id)
        except Exception as e:
            logger.warning("Langfuse get_trace_url failed: %s", e)
            return None


class LLMInterface:
    def __init__(self, model: str, temperature: float, max_tokens: int):
        self.llm = ChatOpenAI(model=model, temperature=temperature, max_completion_tokens=max_tokens)

        lf_secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
        lf_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
        lf_api_key = os.environ.get("LANGFUSE_API_KEY")
        lf_host = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_API_URL")
        self._langfuse = None
        configured = any((lf_secret_key, lf_public_key, lf_api_key))
        logger.info(
            "LLMInterface init: langfuse configured=%s secret_key_set=%s public_key_set=%s api_key_set=%s host=%s",
            configured,
            bool(lf_secret_key),
            bool(lf_public_key),
            bool(lf_api_key),
            lf_host,
        )
        if configured:
            try:
                self._langfuse = LangfuseAdapter(
                    api_key=lf_api_key,
                    secret_key=lf_secret_key,
                    public_key=lf_public_key,
                    host=lf_host,
                )
            except Exception:
                logger.exception("Failed to initialize LangfuseAdapter")
        else:
            logger.warning(
                "LANGFUSE credentials not set; set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY, or legacy LANGFUSE_API_KEY to enable Langfuse tracing"
            )

    def _extract_text(self, result) -> str:
        try:
            first_gen = result.generations[0][0]
            if hasattr(first_gen, "message"):
                return first_gen.message.content
            if hasattr(first_gen, "text"):
                return first_gen.text
        except Exception:
            pass
        return str(result)

    def _extract_token_usage(self, result) -> dict:
        if hasattr(result, "llm_output") and isinstance(result.llm_output, dict):
            for key in ("token_usage", "usage", "token_usage_total"):
                if key in result.llm_output and isinstance(result.llm_output[key], dict):
                    return result.llm_output[key]
        return {}

    def _extract_run_info(self, result) -> dict:
        info = {}
        if hasattr(result, "run") and result.run:
            first_run = result.run[0]
            if hasattr(first_run, "run_id"):
                info["run_id"] = str(first_run.run_id)
        return info

    def generate(self, user_message: str, system_prompt: Optional[str] = None, trace_metadata: Optional[dict] = None) -> str:
        messages = []
        if system_prompt is not None:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_message))

        trace_metadata = trace_metadata or {}
        model_name = getattr(self.llm, "model", "unknown")
        model_parameters = {
            "temperature": getattr(self.llm, "temperature", None),
            "max_tokens": getattr(self.llm, "max_tokens", None),
        }
        completion_start_time = datetime.now(timezone.utc)

        generation_context = (
            self._langfuse.start_generation(
                name="llm.generate",
                prompt=user_message,
                model=model_name,
                metadata=trace_metadata,
                model_parameters=model_parameters,
                completion_start_time=completion_start_time,
            )
            if self._langfuse
            else nullcontext(None)
        )

        with generation_context as generation:
            result = self.llm.generate([messages], metadata=trace_metadata)
            response_text = self._extract_text(result)
            token_usage = self._extract_token_usage(result)
            run_info = self._extract_run_info(result)
            combined_metadata = {**trace_metadata, **run_info}
            if self._langfuse:
                self._langfuse.update_generation(
                    generation,
                    output=response_text,
                    token_usage=token_usage,
                    metadata=combined_metadata,
                )

        if self._langfuse:
            trace_url = self._langfuse.get_trace_url()
            if trace_url:
                logger.info("Langfuse trace URL: %s", trace_url)

        return response_text

    def generate_with_history(self, messages: list, system_prompt: Optional[str] = None, trace_metadata: Optional[dict] = None) -> str:
        lc_messages = []
        if system_prompt is not None:
            lc_messages.append(SystemMessage(content=system_prompt))
        for m in messages:
            if hasattr(m, 'type'):
                lc_messages.append(m)
            elif isinstance(m, dict):
                content = m.get('content', '')
                if m.get('role') == 'user':
                    lc_messages.append(HumanMessage(content=content))
                elif m.get('role') == 'assistant':
                    lc_messages.append(AIMessage(content=content))

        trace_metadata = trace_metadata or {}
        prompt_text = "\n".join([
            str(m.content) if hasattr(m, 'type') else str(m.get('content', ''))
            for m in messages
            if (hasattr(m, 'type') and m.type == 'human') or (isinstance(m, dict) and m.get('role') == 'user')
        ])
        model_name = getattr(self.llm, "model", "unknown")
        model_parameters = {
            "temperature": getattr(self.llm, "temperature", None),
            "max_tokens": getattr(self.llm, "max_tokens", None),
        }
        completion_start_time = datetime.now(timezone.utc)

        generation_context = (
            self._langfuse.start_generation(
                name="llm.generate_with_history",
                prompt=prompt_text,
                model=model_name,
                metadata={**trace_metadata, "history_len": len(messages)},
                model_parameters=model_parameters,
                completion_start_time=completion_start_time,
            )
            if self._langfuse
            else nullcontext(None)
        )

        with generation_context as generation:
            result = self.llm.generate([lc_messages], metadata=trace_metadata)
            response_text = self._extract_text(result)
            token_usage = self._extract_token_usage(result)
            run_info = self._extract_run_info(result)
            combined_metadata = {**trace_metadata, **run_info, "history_len": len(messages)}
            if self._langfuse:
                self._langfuse.update_generation(
                    generation,
                    output=response_text,
                    token_usage=token_usage,
                    metadata=combined_metadata,
                )

        if self._langfuse:
            trace_url = self._langfuse.get_trace_url()
            if trace_url:
                logger.info("Langfuse trace URL: %s", trace_url)

        return response_text
