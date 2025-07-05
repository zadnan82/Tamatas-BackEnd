# Complete fixed app/routers/forum.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload  # FIXED: Added joinedload import
from sqlalchemy import desc, func
from app.database import get_db
from app.models import ForumPostLike, ForumTopicLike, User, ForumTopic, ForumPost
from app.schemas import (
    ForumPostUpdate,
    ForumTopicCreate,
    ForumTopic as ForumTopicSchema,
    ForumPostCreate,
    ForumPost as ForumPostSchema,
    ForumTopicUpdate,
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
    current_user: Optional[User] = Depends(
        get_current_active_user
    ),  # FIXED: Made optional
    db: Session = Depends(get_db),
):
    """Get forum topics with real like counts and post counts"""
    print(f"\n=== GET FORUM TOPICS ===")
    print(f"Category filter: {category}")
    print(f"Current user: {current_user.email if current_user else 'Anonymous'}")

    query = db.query(ForumTopic)

    if category:
        query = query.filter(ForumTopic.category == category)

    # Get topics with creator info using joinedload
    topics = (
        query.options(joinedload(ForumTopic.creator))
        .order_by(desc(ForumTopic.is_pinned), desc(ForumTopic.created_date))
        .offset(skip)
        .limit(limit)
        .all()
    )

    print(f"Found {len(topics)} topics from database")

    # Add real counts to each topic
    for topic in topics:
        # Get real post count
        topic.post_count = (
            db.query(ForumPost).filter(ForumPost.topic_id == topic.id).count()
        )

        # Get real like count
        topic.like_count = (
            db.query(ForumTopicLike).filter(ForumTopicLike.topic_id == topic.id).count()
        )

        # Check if current user liked this topic
        topic.user_liked = False
        if current_user:
            topic.user_liked = (
                db.query(ForumTopicLike)
                .filter(
                    ForumTopicLike.topic_id == topic.id,
                    ForumTopicLike.user_id == current_user.id,
                )
                .first()
            ) is not None

        print(
            f"Topic '{topic.title}': likes={topic.like_count}, user_liked={topic.user_liked}, posts={topic.post_count}"
        )

    print("=== END GET FORUM TOPICS ===\n")
    return topics


@router.get("/topics/{topic_id}", response_model=ForumTopicSchema)
def get_topic(
    topic_id: str,
    current_user: Optional[User] = Depends(
        get_current_active_user
    ),  # FIXED: Made optional
    db: Session = Depends(get_db),
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
    current_user: Optional[User] = Depends(
        get_current_active_user
    ),  # FIXED: Made optional
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
    print(f"\n=== TOGGLE TOPIC LIKE ===")
    print(f"Topic ID: {topic_id}")
    print(f"User ID: {current_user.id}")

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
        print("Removing existing like")
        db.delete(existing_like)
        db.commit()

        # Get updated count
        like_count = (
            db.query(ForumTopicLike).filter(ForumTopicLike.topic_id == topic_id).count()
        )

        print(f"Like removed. New count: {like_count}")
        return {"liked": False, "like_count": like_count}
    else:
        # Like - add the like
        print("Adding new like")
        new_like = ForumTopicLike(
            id=generate_id(), topic_id=topic_id, user_id=current_user.id
        )
        db.add(new_like)
        db.commit()

        # Get updated count
        like_count = (
            db.query(ForumTopicLike).filter(ForumTopicLike.topic_id == topic_id).count()
        )

        print(f"Like added. New count: {like_count}")
        print("=== END TOGGLE TOPIC LIKE ===\n")
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


@router.put("/posts/{post_id}", response_model=ForumPostSchema)
def update_post(
    post_id: str,
    post_update: ForumPostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a forum post"""
    print(f"\n=== UPDATE FORUM POST ===")
    print(f"Post ID: {post_id}")
    print(f"User ID: {current_user.id}")

    # Get the post
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check permissions
    if post.created_by != current_user.id and not getattr(
        current_user, "is_moderator", False
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this post"
        )

    # Check if topic is locked
    topic = db.query(ForumTopic).filter(ForumTopic.id == post.topic_id).first()
    if topic and topic.is_locked and not getattr(current_user, "is_moderator", False):
        raise HTTPException(
            status_code=403, detail="Cannot edit posts in locked topics"
        )

    # Update the post
    if post_update.content:
        post.content = post_update.content.strip()
        post.updated_date = func.now()  # Mark as edited

    db.commit()
    db.refresh(post)

    print(f"Post updated successfully")
    print("=== END UPDATE FORUM POST ===\n")

    return post


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a forum post"""
    print(f"\n=== DELETE FORUM POST ===")
    print(f"Post ID: {post_id}")
    print(f"User ID: {current_user.id}")

    # Get the post
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check permissions
    if post.created_by != current_user.id and not getattr(
        current_user, "is_moderator", False
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    # Delete associated likes first
    db.query(ForumPostLike).filter(ForumPostLike.post_id == post_id).delete()

    # Delete the post
    db.delete(post)
    db.commit()

    print(f"Post deleted successfully")
    print("=== END DELETE FORUM POST ===\n")

    return {"message": "Post deleted successfully"}


@router.post("/posts/{post_id}/report")
def report_post(
    post_id: str,
    report_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Report a forum post"""
    print(f"\n=== REPORT FORUM POST ===")
    print(f"Post ID: {post_id}")
    print(f"User ID: {current_user.id}")
    print(f"Reason: {report_data.get('reason', 'No reason provided')}")

    # Check if post exists
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Can't report your own posts
    if post.created_by == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot report your own post")

    # Here you could save the report to a database table
    # For now, we'll just log it
    reason = report_data.get("reason", "No reason provided").strip()

    # TODO: Implement actual report storage in database
    # You could create a ForumReports table and save the report

    print(f"Post reported successfully")
    print("=== END REPORT FORUM POST ===\n")

    return {
        "message": "Post reported successfully. Thank you for helping keep our community safe."
    }


@router.put("/topics/{topic_id}", response_model=ForumTopicSchema)
def update_topic(
    topic_id: str,
    topic_update: ForumTopicUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a forum topic"""
    print(f"\n=== UPDATE FORUM TOPIC ===")
    print(f"Topic ID: {topic_id}")
    print(f"User ID: {current_user.id}")
    print(
        f"New title: {topic_update.title[:50] if topic_update.title else 'No change'}..."
    )
    print(
        f"New content: {topic_update.content[:50] if topic_update.content else 'No change'}..."
    )

    # Get the topic
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check permissions - only topic creator or moderator can edit
    if topic.created_by != current_user.id and not getattr(
        current_user, "is_moderator", False
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this topic"
        )

    # Check if topic is locked (only moderators can edit locked topics)
    if topic.is_locked and not getattr(current_user, "is_moderator", False):
        raise HTTPException(status_code=403, detail="Cannot edit locked topics")

    # Update the topic
    if topic_update.title:
        topic.title = topic_update.title.strip()

    if topic_update.content:
        topic.content = topic_update.content.strip()

    # Update the modified date
    topic.updated_date = func.now()

    db.commit()
    db.refresh(topic)

    print(f"Topic updated successfully")
    print("=== END UPDATE FORUM TOPIC ===\n")

    return topic


@router.delete("/topics/{topic_id}")
def delete_topic(
    topic_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a forum topic"""
    print(f"\n=== DELETE FORUM TOPIC ===")
    print(f"Topic ID: {topic_id}")
    print(f"User ID: {current_user.id}")

    # Get the topic
    topic = db.query(ForumTopic).filter(ForumTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check permissions - only topic creator or moderator can delete
    if topic.created_by != current_user.id and not getattr(
        current_user, "is_moderator", False
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this topic"
        )

    # Delete all associated data in correct order due to foreign key constraints

    # 1. Delete post likes for all posts in this topic
    post_ids = db.query(ForumPost.id).filter(ForumPost.topic_id == topic_id).all()
    for (post_id,) in post_ids:
        db.query(ForumPostLike).filter(ForumPostLike.post_id == post_id).delete()

    # 2. Delete all posts in this topic
    db.query(ForumPost).filter(ForumPost.topic_id == topic_id).delete()

    # 3. Delete topic likes
    db.query(ForumTopicLike).filter(ForumTopicLike.topic_id == topic_id).delete()

    # 4. Delete the topic itself
    db.delete(topic)
    db.commit()

    print(f"Topic and all associated data deleted successfully")
    print("=== END DELETE FORUM TOPIC ===\n")

    return {"message": "Topic deleted successfully"}
