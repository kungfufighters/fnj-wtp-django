import json
import pytest
from unittest.mock import AsyncMock, patch
from asgiref.sync import sync_to_async
from ..models import Opportunity, Workspace
from ..consumers import VotingConsumer



@pytest.mark.django_db
@pytest.mark.asyncio
async def test_mad_outlier_detection():
    workspace = await sync_to_async(Workspace.objects.create)(
        outlier_threshold=1.5
    )
    opportunity = await sync_to_async(Opportunity.objects.create)(
        opportunity_id=1,
        workspace=workspace
    )

    data = [2, 3, 1, 4, 0]
    opportunity_id = opportunity.opportunity_id

    consumer = VotingConsumer()
    limits = await consumer.mad_outlier_detection(data, opportunity_id)

    assert limits is not False
    lower, upper, median = limits
    assert isinstance(lower, float)
    assert isinstance(upper, float)
    assert isinstance(median, float)
    assert lower < median < upper


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_mad_outlier_detection_no_data():
    consumer = VotingConsumer()
    result = await consumer.mad_outlier_detection([], 9999)
    assert result is False

@pytest.mark.asyncio
@patch("wheretoplayApp.consumers.VotingConsumer.get_votes", new_callable=AsyncMock)
@patch("wheretoplayApp.consumers.VotingConsumer.send", new_callable=AsyncMock)
async def test_broadcast_protocol(mock_send, mock_get_votes):

    mock_get_votes.return_value = {"user_1": 5, "user_2": 3}

    consumer = VotingConsumer()

    event = {
        "criteria_id": 1,
        "session_id": "1234",
        "opportunity_id": 42
    }

    await consumer.broadcast_protocol(event)

    mock_get_votes.assert_awaited_once_with(1, "1234", 42)
    mock_send.assert_awaited_once_with(
        text_data=json.dumps({
            'notification': 'Broadcast results',
            'result': {"user_1": 5, "user_2": 3},
            'criteria_id': 1
        })
    )
