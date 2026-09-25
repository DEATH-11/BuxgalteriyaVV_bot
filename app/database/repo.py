import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Drug, Spek, SpekCounter


async def get_all_drugs(session: AsyncSession) -> list[Drug]:
    result = await session.execute(select(Drug).order_by(Drug.name))
    return list(result.scalars().all())


async def get_drug(session: AsyncSession, drug_id: int) -> Drug | None:
    result = await session.execute(select(Drug).where(Drug.id == drug_id))
    return result.scalar_one_or_none()


async def add_drug(session: AsyncSession, name: str, unit: str, price: float) -> Drug:
    drug = Drug(name=name, unit=unit, price=price)
    session.add(drug)
    await session.commit()
    await session.refresh(drug)
    return drug


async def update_drug(
    session: AsyncSession, drug_id: int, name: str, unit: str, price: float
) -> None:
    drug = await get_drug(session, drug_id)
    if drug:
        drug.name = name
        drug.unit = unit
        drug.price = price
        await session.commit()


async def delete_drug(session: AsyncSession, drug_id: int) -> None:
    drug = await get_drug(session, drug_id)
    if drug:
        await session.delete(drug)
        await session.commit()


async def next_spek_number(session: AsyncSession) -> int:
    result = await session.execute(select(SpekCounter))
    counter = result.scalar_one_or_none()
    if counter is None:
        counter = SpekCounter(last_number=0)
        session.add(counter)
        await session.commit()
        await session.refresh(counter)

    counter.last_number += 1
    await session.commit()
    return counter.last_number


async def save_spek(
    session: AsyncSession,
    user_id: int,
    user_name: str,
    items: list,
    total: float,
) -> Spek:
    number = await next_spek_number(session)
    spek = Spek(
        number=number,
        user_id=user_id,
        user_name=user_name,
        items_json=json.dumps(items, ensure_ascii=False),
        total=total,
    )
    session.add(spek)
    await session.commit()
    await session.refresh(spek)
    return spek


async def get_all_speks(session: AsyncSession, limit: int = 100) -> list[Spek]:
    result = await session.execute(
        select(Spek).order_by(Spek.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_spek_by_number(session: AsyncSession, number: int) -> Spek | None:
    result = await session.execute(select(Spek).where(Spek.number == number))
    return result.scalar_one_or_none()
