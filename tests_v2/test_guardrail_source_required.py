from __future__ import annotations

import pytest

from clubos2.guardrails.source_required import SourceMissingError, requires_source


class _MockRow:
    def __init__(self, source: str | None):
        self.source = source


@pytest.mark.asyncio
async def test_populated_source_passes():
    @requires_source
    async def good_tool():
        return [_MockRow(source="data/gold.csv"), _MockRow(source="docs/file.md")]

    result = await good_tool()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_empty_string_source_raises():
    @requires_source
    async def bad_tool():
        return [_MockRow(source="")]

    with pytest.raises(SourceMissingError, match="without populated source"):
        await bad_tool()


@pytest.mark.asyncio
async def test_none_source_raises():
    @requires_source
    async def bad_tool():
        return [_MockRow(source=None)]

    with pytest.raises(SourceMissingError):
        await bad_tool()


@pytest.mark.asyncio
async def test_single_item_validated():
    @requires_source
    async def single_item_tool():
        return _MockRow(source="")

    with pytest.raises(SourceMissingError):
        await single_item_tool()


@pytest.mark.asyncio
async def test_decorator_preserves_return_value():
    @requires_source
    async def good_tool():
        return [_MockRow(source="data/gold.csv")]

    result = await good_tool()
    assert result[0].source == "data/gold.csv"


@pytest.mark.asyncio
async def test_no_source_attr_passes():
    """Objects without a source attribute are not validated — they're not tool outputs."""
    @requires_source
    async def other_tool():
        return [{"value": 42}]  # plain dict, no source attr

    result = await other_tool()
    assert len(result) == 1
