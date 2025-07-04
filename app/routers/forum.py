from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import ForumPostLike, ForumTopicLike, User, ForumTopic, ForumPost
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
def get_topic(
    topic_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # THIS LINE MIGHT BE MISSING
):
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Increment view count
    topic.view_count += 1

    # Get like count and user's like status
    like_count = (
        db.query(ForumTopicLike).filter(ForumTopicLike.topic_id == topic_id).count()
    )
    user_liked = False
    if current_user:
        user_liked = (
            db.query(ForumTopicLike)
            .filter(
                ForumTopicLike.topic_id == topic_id,
                ForumTopicLike.user_id == current_user.id,
            )
            .first()
        ) is not None

    # Add like data to topic
    topic.like_count = like_count
    topic.user_liked = user_liked

    db.commit()
    return topic


@router.get("/topics/{topic_id}/posts", response_model=List[ForumPostSchema])
def get_topic_posts(
    topic_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),  # THIS LINE MIGHT BE MISSING
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

    # Add like data to each post
    for post in posts:
        like_count = (
            db.query(ForumPostLike).filter(ForumPostLike.post_id == post.id).count()
        )
        user_liked = False
        if current_user:
            user_liked = (
                db.query(ForumPostLike)
                .filter(
                    ForumPostLike.post_id == post.id,
                    ForumPostLike.user_id == current_user.id,
                )
                .first()
            ) is not None

        post.like_count = like_count
        post.user_liked = user_liked

    return posts


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


@router.post("/topics/{topic_id}/like")
def toggle_topic_like(
    topic_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Check if topic exists
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check if user already liked this topic
    existing_like = (
        db.query(ForumTopicLike)
        .filter(
            ForumTopicLike.topic_id == topic_id,
            ForumTopicLike.user_id == current_user.id,
        )
        .first()
    )

    if existing_like:
        # Unlike - remove the like
        db.delete(existing_like)
        db.commit()

        # Get updated count
        like_count = (
            db.query(ForumTopicLike).filter(ForumTopicLike.topic_id == topic_id).count()
        )

        return {"liked": False, "like_count": like_count}
    else:
        # Like - add the like
        new_like = ForumTopicLike(
            id=generate_id(), topic_id=topic_id, user_id=current_user.id
        )
        db.add(new_like)
        db.commit()

        # Get updated count
        like_count = (
            db.query(ForumTopicLike).filter(ForumTopicLike.topic_id == topic_id).count()
        )

        return {"liked": True, "like_count": like_count}


@router.post("/posts/{post_id}/like")
def toggle_post_like(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Check if post exists
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if user already liked this post
    existing_like = (
        db.query(ForumPostLike)
        .filter(
            ForumPostLike.post_id == post_id, ForumPostLike.user_id == current_user.id
        )
        .first()
    )

    if existing_like:
        # Unlike - remove the like
        db.delete(existing_like)
        db.commit()

        # Get updated count
        like_count = (
            db.query(ForumPostLike).filter(ForumPostLike.post_id == post_id).count()
        )

        return {"liked": False, "like_count": like_count}
    else:
        # Like - add the like
        new_like = ForumPostLike(
            id=generate_id(), post_id=post_id, user_id=current_user.id
        )
        db.add(new_like)
        db.commit()

        # Get updated count
        like_count = (
            db.query(ForumPostLike).filter(ForumPostLike.post_id == post_id).count()
        )

        return {"liked": True, "like_count": like_count}
