from datetime import date

import pytest

from nonebot_plugin_dst_management.database import (
    create_sign_record,
    create_sign_reward,
    create_user_binding,
    get_sign_record,
    get_sign_reward,
    get_user_binding,
    init_db,
    list_sign_records,
    list_sign_rewards,
    set_db_path,
    update_user_sign_stats,
)
from nonebot_plugin_dst_management.database.connection import get_db_path


@pytest.fixture
async def db_path(tmp_path):
    original = get_db_path()
    db_file = tmp_path / "sign.db"
    set_db_path(db_file)
    await init_db()
    yield db_file
    set_db_path(original)


@pytest.mark.asyncio
async def test_user_binding_crud(db_path):
    user_id = await create_user_binding("123", "KU_TEST", 1, "player")
    assert user_id is not None

    user = await get_user_binding("123", 1)
    assert user is not None
    assert user.ku_id == "KU_TEST"
    assert user.player_name == "player"

    sign_day = date(2026, 2, 5)
    updated = await update_user_sign_stats("123", 1, sign_day, 3, 2, 1, 10)
    assert updated == 1

    user = await get_user_binding("123", 1)
    assert user is not None
    assert user.last_sign_time == sign_day
    assert user.sign_count == 3
    assert user.continuous_days == 2
    assert user.level == 1
    assert user.total_points == 10


@pytest.mark.asyncio
async def test_sign_record_crud(db_path):
    await create_user_binding("234", "KU_TEST_2", 2, "player2")
    sign_day = date(2026, 2, 5)
    record_id = await create_sign_record(
        "234",
        2,
        sign_day,
        1,
        [{"prefab": "goldnugget", "amount": 10}],
    )
    assert record_id is not None

    record = await get_sign_record("234", sign_day, room_id=2)
    assert record is not None
    assert record.reward_level == 1
    assert record.reward_items
    assert record.reward_items[0]["prefab"] == "goldnugget"

    records = await list_sign_records("234", 2)
    assert len(records) == 1

    duplicate = await create_sign_record(
        "234",
        2,
        sign_day,
        1,
        [{"prefab": "goldnugget", "amount": 10}],
    )
    assert duplicate is None


@pytest.mark.asyncio
async def test_sign_reward_crud(db_path):
    reward_id = await create_sign_reward(
        1,
        0,
        [{"prefab": "goldnugget", "amount": 10}],
        bonus_points=10,
        description="newbie",
    )
    assert reward_id is not None

    reward = await get_sign_reward(1)
    assert reward is not None
    assert reward.bonus_points == 10
    assert reward.reward_items[0]["prefab"] == "goldnugget"

    rewards = await list_sign_rewards()
    assert len(rewards) == 1
