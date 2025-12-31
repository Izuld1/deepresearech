
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from interface_DB.MySQL_knowledge_space import KnowledgeSpace

MAX_KNOWLEDGE_SPACES_PER_USER = 10


# ---------- Create ----------
def create_knowledge_space(
    db: Session,
    *,
    name: str,
    description: str | None,
    owner_id: int,
) -> KnowledgeSpace:
    # 限额校验（为前端留好错误语义）
    count = db.scalar(
        select(func.count()).where(KnowledgeSpace.owner_id == owner_id)
    )
    if count >= MAX_KNOWLEDGE_SPACES_PER_USER:
        raise ValueError("Knowledge space limit reached (max 10)")

    ks = KnowledgeSpace(
        name=name,
        description=description,
        owner_id=owner_id,
    )
    db.add(ks)
    db.commit()
    db.refresh(ks)
    return ks


# ---------- Read (list) ----------
def list_knowledge_spaces(
    db: Session,
    *,
    owner_id: int,
) -> list[KnowledgeSpace]:
    return db.scalars(
        select(KnowledgeSpace)
        .where(KnowledgeSpace.owner_id == owner_id)
        .order_by(KnowledgeSpace.created_at.desc())
    ).all()


# ---------- Read (single) ----------
def get_knowledge_space(
    db: Session,
    *,
    knowledge_space_id: int,
    owner_id: int,
) -> KnowledgeSpace | None:
    return db.scalar(
        select(KnowledgeSpace).where(
            KnowledgeSpace.id == knowledge_space_id,
            KnowledgeSpace.owner_id == owner_id,
        )
    )


# ---------- Update ----------
def update_knowledge_space(
    db: Session,
    *,
    knowledge_space_id: int,
    owner_id: int,
    name: str | None = None,
    description: str | None = None,
    visibility: str | None = None,
) -> KnowledgeSpace:
    ks = get_knowledge_space(
        db,
        knowledge_space_id=knowledge_space_id,
        owner_id=owner_id,
    )
    if not ks:
        raise ValueError("Knowledge space not found")

    if name is not None:
        ks.name = name
    if description is not None:
        ks.description = description
    if visibility is not None:
        ks.visibility = visibility

    db.commit()
    db.refresh(ks)
    return ks


# ---------- Delete ----------
def delete_knowledge_space(
    db: Session,
    *,
    knowledge_space_id: int,
    owner_id: int,
) -> None:
    ks = get_knowledge_space(
        db,
        knowledge_space_id=knowledge_space_id,
        owner_id=owner_id,
    )
    if not ks:
        raise ValueError("Knowledge space not found")

    db.delete(ks)
    db.commit()
