from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import User, ForumTopic, ForumPost
from app.schemas import (
    ForumTopicCreate,
    ForumTopic as ForumTopicSchema,
    ForumPostCreate,
    ForumPost as ForumPostSchema,
)
from app.auth import get_current_active_user
from app.utils import generate_id

router = APIRouter(prefix="/forum", tags=["forum"])


@router.post("/topics", response_model=ForumTopicSchema)
def create_topic(
    topic: ForumTopicCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db_topic = ForumTopic(id=generate_id(), **topic.dict(), created_by=current_user.id)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


@router.get("/topics", response_model=List[ForumTopicSchema])
def get_topics(
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(ForumTopic)

    if category:
        query = query.filter(ForumTopic.category == category)

    # Add post count
    query = query.outerjoin(ForumPost).group_by(ForumTopic.id)
    topics = (
        query.order_by(desc(ForumTopic.is_pinned), desc(ForumTopic.created_date))
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Add post count to each topic
    for topic in topics:
        topic.post_count = (
            db.query(ForumPost).filter(ForumPost.topic_id == topic.id).count()
        )

    return topics


@router.get("/topics/{topic_id}", response_model=ForumTopicSchema)
def get_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Increment view count
    topic.view_count += 1
    db.commit()

    return topic


@router.post("/posts", response_model=ForumPostSchema)
def create_post(
    post: ForumPostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Verify topic exists
    topic = db.query(ForumTopic).filter(ForumTopic.id == post.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.is_locked:
        raise HTTPException(status_code=403, detail="Topic is locked")

    db_post = ForumPost(id=generate_id(), **post.dict(), created_by=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.get("/topics/{topic_id}/posts", response_model=List[ForumPostSchema])
def get_topic_posts(
    topic_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    posts = (
        db.query(ForumPost)
        .filter(ForumPost.topic_id == topic_id)
        .order_by(ForumPost.created_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return posts
