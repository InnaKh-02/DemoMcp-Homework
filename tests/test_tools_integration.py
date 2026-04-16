import pytest
from fastmcp import Client, FastMCP


@pytest.mark.asyncio
async def test_get_issue_valid(mcp):
    async with Client(mcp) as client:
        result = await client.call_tool_mcp("get_issue", {"issue_key": "DEV-1"})

    assert result.isError is False
    assert result.structuredContent["key"] == "DEV-1"
    assert "summary" in result.structuredContent
    assert "status" in result.structuredContent


@pytest.mark.asyncio
async def test_get_issue_invalid_format(mcp):
    async with Client(mcp) as client:
        result = await client.call_tool_mcp("get_issue", {"issue_key": "DEV1"})

    assert result.isError is True
    assert "Invalid issue key format" in result.content[0].text


@pytest.mark.asyncio
async def test_create_issue_empty_summary(mcp):
    async with Client(mcp) as client:
        result = await client.call_tool_mcp(
            "create_issue",
            {"summary": "", "description": "desc", "issue_type": "Task"},
        )

    assert result.isError is True
    assert "summary" in result.content[0].text.lower()


@pytest.mark.asyncio
async def test_add_comment_response_fields_are_correct(mcp):
    async with Client(mcp) as client:
        result = await client.call_tool_mcp(
            "add_comment",
            {"issue_key": "DEV-1", "comment": "integration test comment"},
        )

    assert result.isError is False
    data = result.structuredContent
    assert "comment_id" in data
    assert "issue_key" in data
    assert "author" in data
    assert isinstance(data["comment_id"], str)
    assert data["comment_id"]
    assert data["issue_key"] == "DEV-1"
    assert data["author"]


@pytest.mark.asyncio
async def test_get_comments_trailing_space(mcp):
    async with Client(mcp) as client:
        result = await client.call_tool_mcp("get_comments", {"issue_key": "DEV-1 "})

    assert result.isError is True
    assert "Invalid issue key format" in result.content[0].text


@pytest.mark.asyncio
async def test_get_comments_leading_space(mcp):
    async with Client(mcp) as client:
        result = await client.call_tool_mcp("get_comments", {"issue_key": " DEV-1"})

    assert result.isError is True
    assert "Invalid issue key format" in result.content[0].text
