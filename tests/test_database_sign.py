from __future__ import annotations

from datetime import date

import pytest

from nonebot_plugin_dst_management.database import (
    create_sign_record,
    create_user_binding,
    get_sign_record,
    init_db,
    list_pending_sign_records,
    set_db_path,
    update_sign_record_status,
)
from nonebot_plugin_dst_management.database.connection import get_db_path


@pytest.fixture
async def db_path(tmp_path):
    original = get_db_path()
    db_file = tmp_path / "sign_pending.db"
    set_db_path(db_file)
    await init_db()
    yield db_file
    set_db_path(original)


@pytest.mark.asyncio
async def test_pending_sign_records_and_status_update(db_path):
    await create_user_binding("300", "KU_TEST1", 1, "player1")
    await create_user_binding("301", "KU_TEST2", 2, "player2")

    sign_day = date(2026, 2, 5)
    record_id = await create_sign_record(
        "300",
        1,
        sign_day,
        1,
        [{"prefab": "goldnugget", "amount": 10}],
        status=0,
    )
    await create_sign_record(
        "301",
        2,
        sign_day,
        1,
        [{"prefab": "cutgrass", "amount": 5}],
        status=1,
    )

    pending = await list_pending_sign_records()
    assert len(pending) == 1
    assert pending[0].id == record_id
    assert pending[0].ku_id == "KU_TEST1"

    updated = await update_sign_record_status(record_id, 1)
    assert updated == 1

    record = await get_sign_record("300", sign_day, room_id=1)
    assert record is not None
    assert record.status == 1

    pending_after = await list_pending_sign_records()
    assert not pending_after
