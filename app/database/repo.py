import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Contract,
    Drug,
    Setting,
    Spek,
    SpekCounter,
    User,
)


# ========== SETTINGS ==========

async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    result = await session.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    result = await session.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting is None:
        session.add(Setting(key=key, value=value))
    else:
        setting.value = value
    await session.commit()


# ========== USERS ==========

async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str,
    last_name: str,
    phone: str,
    region: str,
    language: str,
    company: str,
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        region=region,
        language=language,
        company=company,
        status="pending",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def set_user_company(
    session: AsyncSession, telegram_id: int, company: str
) -> None:
    user = await get_user(session, telegram_id)
    if user:
        user.company = company
        await session.commit()


async def set_user_status(
    session: AsyncSession, telegram_id: int, status: str
) -> None:
    user = await get_user(session, telegram_id)
    if user:
        user.status = status
        await session.commit()


async def get_all_users(
    session: AsyncSession, status: str | None = None, limit: int = 200
) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(User.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_users_by_company(
    session: AsyncSession, company: str, status: str | None = None
) -> list[User]:
    stmt = (
        select(User)
        .where(User.company == company)
        .order_by(User.created_at.desc())
    )
    if status:
        stmt = stmt.where(User.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_user(session: AsyncSession, telegram_id: int) -> None:
    user = await get_user(session, telegram_id)
    if user:
        await session.delete(user)
        await session.commit()


async def count_users_by_status(session: AsyncSession) -> dict:
    result = await session.execute(
        select(User.status, func.count()).group_by(User.status)
    )
    return {row[0]: row[1] for row in result.all()}


# ========== DRUGS ==========

async def get_drugs_by_company(
    session: AsyncSession, company: str
) -> list[Drug]:
    result = await session.execute(
        select(Drug).where(Drug.company == company).order_by(Drug.name)
    )
    return list(result.scalars().all())


async def get_drug(session: AsyncSession, drug_id: int) -> Drug | None:
    result = await session.execute(select(Drug).where(Drug.id == drug_id))
    return result.scalar_one_or_none()


async def add_drug(
    session: AsyncSession, company: str, name: str, unit: str, price: float
) -> Drug:
    drug = Drug(company=company, name=name, unit=unit, price=price)
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


# ========== SPEKS ==========

async def next_spek_number(session: AsyncSession, company: str) -> int:
    result = await session.execute(
        select(SpekCounter).where(SpekCounter.company == company)
    )
    counter = result.scalar_one_or_none()
    if counter is None:
        counter = SpekCounter(company=company, last_number=0)
        session.add(counter)
        await session.commit()
        await session.refresh(counter)

    counter.last_number += 1
    await session.commit()
    return counter.last_number


async def get_spek_counter(session: AsyncSession, company: str) -> int:
    result = await session.execute(
        select(SpekCounter).where(SpekCounter.company == company)
    )
    counter = result.scalar_one_or_none()
    return counter.last_number if counter else 0


async def set_spek_counter(
    session: AsyncSession, company: str, value: int
) -> None:
    result = await session.execute(
        select(SpekCounter).where(SpekCounter.company == company)
    )
    counter = result.scalar_one_or_none()
    if counter is None:
        counter = SpekCounter(company=company, last_number=value)
        session.add(counter)
    else:
        counter.last_number = value
    await session.commit()


async def save_spek(
    session: AsyncSession,
    company: str,
    user_id: int,
    user_name: str,
    items: list,
    total: float,
) -> Spek:
    number = await next_spek_number(session, company)
    spek = Spek(
        company=company,
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


async def get_all_speks(
    session: AsyncSession, company: str | None = None, limit: int = 100
) -> list[Spek]:
    stmt = select(Spek).order_by(Spek.created_at.desc()).limit(limit)
    if company:
        stmt = stmt.where(Spek.company == company)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_spek(session: AsyncSession, spek_id: int) -> Spek | None:
    result = await session.execute(select(Spek).where(Spek.id == spek_id))
    return result.scalar_one_or_none()


# ========== CONTRACTS ==========

async def get_contract_prefix(session: AsyncSession, company: str) -> str:
    return await get_setting(session, f"contract_prefix_{company}", "1/26")


async def set_contract_prefix(
    session: AsyncSession, company: str, value: str
) -> None:
    await set_setting(session, f"contract_prefix_{company}", value)


async def next_contract_number(session: AsyncSession, company: str) -> str:
    current = await get_setting(session, f"contract_prefix_{company}", "1/26")
    try:
        if "/" in current:
            num_part, suffix = current.split("/", 1)
            new_num = int(num_part) + 1
            new_value = f"{new_num}/{suffix}"
        else:
            new_value = str(int(current) + 1)
    except ValueError:
        new_value = current

    await set_setting(session, f"contract_prefix_{company}", new_value)
    return new_value


async def save_contract(
    session: AsyncSession,
    company: str,
    inn: str,
    firma: str,
    number: str,
    date: str,
    user_id: int,
    user_name: str,
    pdf_data: bytes | None,
    pdf_name: str,
) -> Contract:
    contract = Contract(
        company=company,
        inn=inn,
        firma=firma,
        number=number,
        date=date,
        user_id=user_id,
        user_name=user_name,
        pdf_data=pdf_data,
        pdf_name=pdf_name,
    )
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract


async def get_contracts_by_inn(
    session: AsyncSession, inn: str, company: str | None = None
) -> list[Contract]:
    stmt = (
        select(Contract)
        .where(Contract.inn == inn)
        .order_by(Contract.created_at.desc())
    )
    if company:
        stmt = stmt.where(Contract.company == company)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_contract(session: AsyncSession, contract_id: int) -> Contract | None:
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    return result.scalar_one_or_none()
