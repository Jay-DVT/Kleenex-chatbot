import pytest
from httpx import AsyncClient
from datetime import datetime, timezone

from app.core.config import settings
from .test_users import SECTION as USER_SECTION

SECTION = "/participations/"
PHONE = "1234567890"
API_URL = settings.BASE_URL + settings.API_STR
FULL_URL = API_URL + SECTION


@pytest.mark.asyncio
async def test_create_participation():
    async with AsyncClient() as client:
        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        await client.delete(API_URL + USER_SECTION + PHONE)


@pytest.mark.asyncio
async def test_fetch_participation_by_id():
    async with AsyncClient() as client:
        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        response = await client.get(FULL_URL + participation["_id"])
        assert response.status_code == 200

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        await client.delete(API_URL + USER_SECTION + PHONE)


@pytest.mark.asyncio
async def test_delete_participation_by_id():
    async with AsyncClient() as client:
        user_phones = ["1234567890", "0987654321"]
        users = [{"phone": phone}
                 for phone in user_phones]

        clients = []
        for user in users:
            response = await client.post(API_URL + USER_SECTION, json=user)
            assert response.status_code == 201
            cl = response.json()
            clients.append(cl)

        response = await client.get(FULL_URL)
        assert response.status_code == 200

        participations = response.json()
        length = len(participations)

        # create 3 participations for each user
        for user in clients:
            for i in range(3):
                response = await client.post(FULL_URL, json={"user": user})
                assert response.status_code == 201

        response = await client.get(FULL_URL)
        assert response.status_code == 200

        participations = response.json()
        assert len(participations) == length + 6

        for participation in participations:
            response = await client.delete(FULL_URL + participation["_id"])
            assert response.status_code == 204

        response = await client.get(FULL_URL)
        assert response.status_code == 200

        participations = response.json()
        assert len(participations) == length

        # delete users
        for user in users:
            response = await client.delete(API_URL + USER_SECTION + user["phone"])
            assert response.status_code == 204


@pytest.mark.asyncio
async def test_update_participation_by_id():
    async with AsyncClient() as client:
        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()
        assert participation["status"] == "INCOMPLETE"
        # valid datetime
        assert datetime.fromisoformat(participation["datetime"])
        assert participation["user"] == user
        assert participation["ticket_url"] is None
        assert participation["ticket_attempts"] == 0
        assert participation["participationNumber"] == -1

        # update participation
        participation["status"] = "COMPLETE"
        participation["ticket_url"] = "https://example.com"
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation["status"] == "COMPLETE"
        assert participation["ticket_url"] == "https://example.com"

        # clean up
        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        response = await client.delete(API_URL + USER_SECTION + PHONE)
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_put_flow_prize():
    async with AsyncClient() as client:
        TICKET_URL = 'https://aws.com/123'
        PARTICIPATION_NO = 123

        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        participation['ticket_url'] = TICKET_URL
        participation['ticket_attempts'] = 1
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1
        assert participation['status'] == 'INCOMPLETE'

        participation['participationNumber'] = PARTICIPATION_NO
        participation['status'] = 'COMPLETE'
        participation['prizeType'] = 'digital'
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] == 'digital'
        assert participation['participationNumber'] == PARTICIPATION_NO

        response = await client.get(FULL_URL + participation["_id"])
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] == 'digital'
        assert participation['participationNumber'] == PARTICIPATION_NO
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        response = await client.delete(API_URL + USER_SECTION + PHONE)
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_put_flow_no_prize():
    async with AsyncClient() as client:
        TICKET_URL = 'https://aws.com/123'

        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        participation['ticket_url'] = TICKET_URL
        participation['ticket_attempts'] = 1
        participation['status'] = 'INCOMPLETE'
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1
        assert participation['status'] == 'INCOMPLETE'

        participation['status'] = 'COMPLETE'
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] is None
        assert participation['participationNumber'] == -1

        response = await client.get(FULL_URL + participation["_id"])
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] is None
        assert participation['participationNumber'] == -1
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        response = await client.delete(API_URL + USER_SECTION + PHONE)
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_participation():
    async with AsyncClient() as client:
        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        await client.delete(API_URL + USER_SECTION + PHONE)


@pytest.mark.asyncio
async def test_fetch_participation_by_id():
    async with AsyncClient() as client:
        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        response = await client.get(FULL_URL + participation["_id"])
        assert response.status_code == 200

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        await client.delete(API_URL + USER_SECTION + PHONE)


@pytest.mark.asyncio
async def test_delete_participation_by_id():
    async with AsyncClient() as client:
        user_phones = ["1234567890", "0987654321"]
        users = [{"phone": phone}
                 for phone in user_phones]

        clients = []
        for user in users:
            response = await client.post(API_URL + USER_SECTION, json=user)
            assert response.status_code == 201
            cl = response.json()
            clients.append(cl)

        response = await client.get(FULL_URL)
        assert response.status_code == 200

        participations = response.json()
        length = len(participations)

        # create 3 participations for each user
        for user in clients:
            for i in range(3):
                response = await client.post(FULL_URL, json={"user": user})
                assert response.status_code == 201

        response = await client.get(FULL_URL)
        assert response.status_code == 200

        participations = response.json()
        assert len(participations) == length + 6

        for participation in participations:
            response = await client.delete(FULL_URL + participation["_id"])
            assert response.status_code == 204

        response = await client.get(FULL_URL)
        assert response.status_code == 200

        participations = response.json()
        assert len(participations) == length

        # delete users
        for user in users:
            response = await client.delete(API_URL + USER_SECTION + user["phone"])
            assert response.status_code == 204


@pytest.mark.asyncio
async def test_update_participation_by_id():
    async with AsyncClient() as client:
        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()
        assert participation["status"] == "INCOMPLETE"
        # valid datetime
        assert datetime.fromisoformat(participation["datetime"])
        assert participation["user"] == user
        assert participation["ticket_url"] is None
        assert participation["ticket_attempts"] == 0
        assert participation["participationNumber"] == -1

        # update participation
        participation["status"] = "COMPLETE"
        participation["ticket_url"] = "https://example.com"
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation["status"] == "COMPLETE"
        assert participation["ticket_url"] == "https://example.com"

        # clean up
        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        response = await client.delete(API_URL + USER_SECTION + PHONE)
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_put_flow_prize():
    async with AsyncClient() as client:
        TICKET_URL = 'https://aws.com/123'
        PARTICIPATION_NO = 123

        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        participation['ticket_url'] = TICKET_URL
        participation['ticket_attempts'] = 1
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1
        assert participation['status'] == 'INCOMPLETE'

        participation['participationNumber'] = PARTICIPATION_NO
        participation['status'] = 'COMPLETE'
        participation['prizeType'] = 'digital'
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] == 'digital'
        assert participation['participationNumber'] == PARTICIPATION_NO

        response = await client.get(FULL_URL + participation["_id"])
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] == 'digital'
        assert participation['participationNumber'] == PARTICIPATION_NO
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        response = await client.delete(API_URL + USER_SECTION + PHONE)
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_put_flow_no_prize():
    async with AsyncClient() as client:
        TICKET_URL = 'https://aws.com/123'

        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE})
        assert response.status_code == 201

        user = response.json()

        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201

        participation = response.json()

        participation['ticket_url'] = TICKET_URL
        participation['ticket_attempts'] = 1
        participation['status'] = 'INCOMPLETE'
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1
        assert participation['status'] == 'INCOMPLETE'

        participation['status'] = 'COMPLETE'
        response = await client.put(FULL_URL + participation["_id"], json=participation)
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] is None
        assert participation['participationNumber'] == -1

        response = await client.get(FULL_URL + participation["_id"])
        assert response.status_code == 200

        participation = response.json()
        assert participation['status'] == 'COMPLETE'
        assert participation['prizeType'] is None
        assert participation['participationNumber'] == -1
        assert participation['ticket_url'] == TICKET_URL
        assert participation['ticket_attempts'] == 1

        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        response = await client.delete(API_URL + USER_SECTION + PHONE)
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_count_participations_by_date():
    async with AsyncClient() as client:
        response = await client.post(API_URL + USER_SECTION, json={"phone": PHONE, "terms": True})
        assert response.status_code == 201

        user = response.json()

        # Create a participation for today
        response = await client.post(FULL_URL, json={"user": user})
        assert response.status_code == 201
        participation = response.json()

        # Count participations for today
        today_str = datetime.now(timezone.utc).date().isoformat()
        response = await client.get(FULL_URL + "count", params={"date": today_str})
        assert response.status_code == 200

        count = response.json()
        assert count["count"] >= 1

        # Clean up
        response = await client.delete(FULL_URL + participation["_id"])
        assert response.status_code == 204

        response = await client.delete(API_URL + USER_SECTION + PHONE)
        assert response.status_code == 204
