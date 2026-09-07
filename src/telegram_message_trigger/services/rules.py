import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from telegram_message_trigger.db.models import Rule, Trigger
from telegram_message_trigger.services.matching import TriggerConflict, scopes_can_overlap, triggers_overlap


def format_target_label(
    user_id: int, first_name: str | None, last_name: str | None, username: str | None
) -> str:
    name = " ".join(part for part in (first_name, last_name) if part)
    if username:
        return f"{name} (@{username})" if name else f"@{username}"
    return name if name else f"ID {user_id}"


def parse_trigger_input(raw_text: str) -> list[str]:
    parts = re.split(r"[\n,]+", raw_text)
    return dedupe_triggers([part.strip() for part in parts if part.strip()])


def dedupe_triggers(trigger_texts: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for text in trigger_texts:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(text)
    return deduped


async def list_rules(session: AsyncSession, owner_id: int) -> list[Rule]:
    stmt = (
        select(Rule)
        .where(Rule.owner_id == owner_id)
        .options(selectinload(Rule.triggers))
        .order_by(Rule.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_active_rules(session: AsyncSession, owner_id: int) -> list[Rule]:
    stmt = (
        select(Rule)
        .where(Rule.owner_id == owner_id, Rule.is_active.is_(True))
        .options(selectinload(Rule.triggers))
        .order_by(Rule.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_rule(session: AsyncSession, rule_id: int) -> Rule | None:
    stmt = select(Rule).where(Rule.id == rule_id).options(selectinload(Rule.triggers))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def find_conflicting_trigger(
    session: AsyncSession,
    owner_id: int,
    case_sensitive: bool,
    whole_word: bool,
    trigger_texts: list[str],
    target_telegram_user_id: int | None = None,
    exclude_rule_id: int | None = None,
) -> TriggerConflict | None:
    stmt = (
        select(Rule)
        .where(Rule.owner_id == owner_id, Rule.is_active.is_(True))
        .options(selectinload(Rule.triggers))
    )
    if exclude_rule_id is not None:
        stmt = stmt.where(Rule.id != exclude_rule_id)
    result = await session.execute(stmt)
    other_rules = result.scalars().all()

    for candidate in trigger_texts:
        for other_rule in other_rules:
            if not scopes_can_overlap(target_telegram_user_id, other_rule.target_telegram_user_id):
                continue
            for other_trigger in other_rule.triggers:
                if triggers_overlap(
                    candidate,
                    case_sensitive,
                    whole_word,
                    other_trigger.text,
                    other_rule.case_sensitive,
                    other_rule.whole_word,
                ):
                    return TriggerConflict(
                        new_trigger=candidate,
                        existing_trigger=other_trigger.text,
                        existing_rule_id=other_rule.id,
                    )
    return None


async def find_conflict_for_rule(session: AsyncSession, rule: Rule) -> TriggerConflict | None:
    return await find_conflicting_trigger(
        session,
        rule.owner_id,
        rule.case_sensitive,
        rule.whole_word,
        [trigger.text for trigger in rule.triggers],
        target_telegram_user_id=rule.target_telegram_user_id,
        exclude_rule_id=rule.id,
    )


async def create_rule(
    session: AsyncSession,
    owner_id: int,
    case_sensitive: bool,
    whole_word: bool,
    trigger_texts: list[str],
    reply_text: str,
    target_telegram_user_id: int | None = None,
    target_label: str | None = None,
) -> Rule:
    rule = Rule(
        owner_id=owner_id,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        reply_text=reply_text,
        is_active=True,
        target_telegram_user_id=target_telegram_user_id,
        target_label=target_label,
        triggers=[Trigger(text=text) for text in trigger_texts],
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def update_rule_matching(session: AsyncSession, rule: Rule, case_sensitive: bool, whole_word: bool) -> None:
    rule.case_sensitive = case_sensitive
    rule.whole_word = whole_word
    await session.commit()


async def update_rule_scope(
    session: AsyncSession, rule: Rule, target_telegram_user_id: int | None, target_label: str | None
) -> None:
    rule.target_telegram_user_id = target_telegram_user_id
    rule.target_label = target_label
    await session.commit()


async def update_rule_triggers(session: AsyncSession, rule: Rule, trigger_texts: list[str]) -> None:
    rule.triggers = [Trigger(text=text) for text in trigger_texts]
    await session.commit()


async def update_rule_reply(session: AsyncSession, rule: Rule, reply_text: str) -> None:
    rule.reply_text = reply_text
    await session.commit()


async def set_rule_active(session: AsyncSession, rule: Rule, is_active: bool) -> None:
    rule.is_active = is_active
    await session.commit()
