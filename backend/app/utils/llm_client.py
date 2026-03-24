"""
LLM客户端封装 - 统一使用OpenAI格式调用
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config


class LLMClient:
    """LLM客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）
            
        Returns:
            模型响应文本
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # Thinking model cleanup (Qwen3.5, MiniMax M2.5, etc.)
        # 1. Strip closed <think>...</think> blocks
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        # 2. Strip unclosed <think>... (truncated by max_tokens)
        content = re.sub(r'<think>[\s\S]*', '', content).strip()
        return content
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse a JSON object from text that may contain thinking/reasoning preamble."""
        # 1. Clean markdown code fences
        cleaned = text.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        # 2. Try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 3. Extract last complete JSON object via brace matching
        last_close = cleaned.rfind('}')
        if last_close != -1:
            depth = 0
            for i in range(last_close, -1, -1):
                if cleaned[i] == '}':
                    depth += 1
                elif cleaned[i] == '{':
                    depth -= 1
                if depth == 0:
                    try:
                        return json.loads(cleaned[i:last_close + 1])
                    except json.JSONDecodeError:
                        break

        raise ValueError(f"LLM返回的JSON格式无效: {cleaned[:500]}")

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 32768
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            解析后的JSON对象
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Try json_object format first; fall back to no format constraint
        # (some providers like LM Studio don't support response_format json_object)
        for attempt_format in [{"type": "json_object"}, None]:
            try:
                call_kwargs = {**kwargs}
                if attempt_format:
                    call_kwargs["response_format"] = attempt_format
                response = self.client.chat.completions.create(**call_kwargs)
                raw = response.choices[0].message.content

                # Strip all forms of thinking output:
                # 1. Closed <think>...</think> blocks
                raw = re.sub(r'<think>[\s\S]*?</think>', '', raw).strip()
                # 2. Unclosed <think>... (truncated by max_tokens)
                raw = re.sub(r'<think>[\s\S]*', '', raw).strip()

                return self._extract_json(raw)
            except ValueError:
                # JSON extraction failed — if we used json_object format, retry without it
                if attempt_format:
                    continue
                raise
            except Exception:
                # API error (e.g. unsupported response_format) — retry without format
                if attempt_format:
                    continue
                raise

