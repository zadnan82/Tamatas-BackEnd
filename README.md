# Fresh Trade Backend

A comprehensive backend API for the Fresh Trade platform - connecting local farmers and gardeners to exchange fresh produce.

## Features

- **User Management**: Registration, authentication, profiles with ratings
- **Product Listings**: Create, update, delete listings with images and location
- **Messaging System**: Direct communication between users
- **Reviews & Ratings**: User feedback and rating system
- **Favorites**: Save interesting listings
- **Forum**: Community discussions
- **Search & Filters**: Advanced filtering by category, location, price
- **File Upload**: Image upload with S3 support
- **Real-time Notifications**: Email notifications for messages

## Tech Stack

- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and Celery broker
- **Celery**: Background task processing
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations
- **Docker**: Containerization
- **AWS S3**: File storage (optional)

## Quick Start

### Using Docker (Recommended)

1. **Clone and setup**:

```bash
git clone <repository>
cd fresh-trade-backend
cp .env.example .env
# Edit .env with your configuration
```

2. **Start services**:

```bash
chmod +x scripts/run_prod.sh
./scripts/run_prod.sh
```

3. **Access the API**:

- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Interactive API: http://localhost:8000/redoc

### Development Setup

1. **Install dependencies**:

```bash
pip install -r requirements.txt
```

2. **Start PostgreSQL and Redis**:

```bash
docker-compose up -d db redis
```

3. **Run migrations**:

```bash
alembic upgrade head
```

4. **Initialize sample data**:

```bash
python scripts/init_db.py
```

5. **Start development server**:

```bash
chmod +x scripts/run_dev.sh
./scripts/run_dev.sh
```

## API Endpoints

### Authentication

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Users

- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user
- `GET /users/{user_id}` - Get user profile
- `GET /users/{user_id}/reviews` - Get user reviews

### Listings

- `POST /listings/` - Create listing
- `GET /listings/` - Get listings (with filters)
- `GET /listings/my` - Get current user's listings
- `GET /listings/feeds` - Get popular/recent listings
- `GET /listings/{listing_id}` - Get listing details
- `PUT /listings/{listing_id}` - Update listing
- `DELETE /listings/{listing_id}` - Delete listing

### Messages

- `POST /messages/` - Send message
- `GET /messages/` - Get user messages
- `GET /messages/conversations/{user_id}` - Get conversation
- `PUT /messages/{message_id}/read` - Mark message as read

### Reviews

- `POST /reviews/` - Create review
- `GET /reviews/user/{user_id}` - Get user reviews

### Favorites

- `POST /favorites/` - Add to favorites
- `GET /favorites/` - Get user favorites
- `DELETE /favorites/{favorite_id}` - Remove favorite

### Forum

- `POST /forum/topics` - Create forum topic
- `GET /forum/topics` - Get forum topics
- `GET /forum/topics/{topic_id}` - Get topic details
- `POST /forum/posts` - Create forum post
- `GET /forum/topics/{topic_id}/posts` - Get topic posts

### File Upload

- `POST /upload/image` - Upload single image
- `POST /upload/images` - Upload multiple images

### Contact

- `POST /contact/` - Send contact form

## Environment Variables

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/fresh_trade
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_BUCKET_NAME=fresh-trade-uploads
AWS_REGION=us-east-1

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Database Schema

The database includes the following main tables:

- `users` - User accounts and profiles
- `listings` - Product listings
- `messages` - User communications
- `reviews` - User ratings and reviews
- `favorites` - Saved listings
- `forum_topics` - Forum discussions
- `forum_posts` - Forum replies

## Background Tasks

Celery handles:

- Email notifications
- View count updates
- Image processing
- Cleanup tasks

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- File upload validation
- CORS protection
- SQL injection prevention

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Deployment

1. **Production environment**:

```bash
# Update .env for production
# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

2. **Database migrations**:

```bash
alembic upgrade head
```

## Support

For issues and questions, please create an issue in the repository or contact the development team.

## License

This project is licensed under the MIT License.
