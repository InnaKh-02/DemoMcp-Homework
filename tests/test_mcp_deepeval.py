import os
import uuid

import pytest
from fastmcp import Client

deepeval = pytest.importorskip("deepeval")
from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig
from deepeval.metrics import MCPUseMetric
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase, MCPServer, MCPToolCall


def _gemini_model_name() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")


def _gemini_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY")


pytestmark = pytest.mark.skipif(
    not _gemini_api_key(),
    reason="GOOGLE_API_KEY is required for DeepEval MCP metrics",
)


def _metric() -> MCPUseMetric:
    gemini_model = GeminiModel(
        model=_gemini_model_name(),
        api_key=_gemini_api_key(),
    )
    return MCPUseMetric(model=gemini_model, threshold=0.5, async_mode=False)


@pytest.mark.asyncio
async def test_deepeval_get_issue_single_turn(mcp):
    async with Client(mcp) as client:
        tools = await client.list_tools()
        result = await client.call_tool_mcp("get_issue", {"issue_key": "DEV-1"})

    assert result.isError is False

    test_case = LLMTestCase(
        input="Get details for issue DEV-1",
        actual_output=str(result.structuredContent),
        mcp_servers=[
            MCPServer(server_name="JiraMCP", transport="stdio", available_tools=tools)
        ],
        mcp_tools_called=[
            MCPToolCall(name="get_issue", args={"issue_key": "DEV-1"}, result=result)
        ],
    )

    eval_result = evaluate(
        [test_case],
        [_metric()],
        async_config=AsyncConfig(run_async=False),
    )
    assert eval_result.test_results[0].success is True


@pytest.mark.asyncio
async def test_deepeval_create_and_delete_issue(mcp):
    summary = f"DeepEval issue {uuid.uuid4().hex[:8]}"

    async with Client(mcp) as client:
        tools = await client.list_tools()
        created = await client.call_tool_mcp(
            "create_issue",
            {
                "summary": summary,
                "description": "Created by DeepEval test",
                "issue_type": "Task",
            },
        )
        assert created.isError is False

        created_key = (created.structuredContent or {}).get("key")
        assert isinstance(created_key, str) and created_key

        deleted = await client.call_tool_mcp(
            "delete_issue",
            {"issue_key": created_key},
        )
        assert deleted.isError is False

    test_case = LLMTestCase(
        input="Create a Task issue and then delete it",
        actual_output=f"create={created.structuredContent}; delete={deleted.structuredContent}",
        mcp_servers=[
            MCPServer(server_name="JiraMCP", transport="stdio", available_tools=tools)
        ],
        mcp_tools_called=[
            MCPToolCall(
                name="create_issue",
                args={
                    "summary": summary,
                    "description": "Created by DeepEval test",
                    "issue_type": "Task",
                },
                result=created,
            ),
            MCPToolCall(
                name="delete_issue",
                args={"issue_key": created_key},
                result=deleted,
            ),
        ],
    )

    eval_result = evaluate(
        [test_case],
        [_metric()],
        async_config=AsyncConfig(run_async=False),
    )
    assert eval_result.test_results[0].success is True
