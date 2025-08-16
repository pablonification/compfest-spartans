"""MongoDB implementation of user repository for SmartBin backend."""

from __future__ import annotations

import logging
from typing import Optional, List
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorCollection

from ..domain.interfaces.user_repository import UserRepository
from ..models.user import User
from ..db.mongo import mongo_db

logger = logging.getLogger(__name__)


class MongoDBUserRepository(UserRepository):
    """MongoDB implementation of user repository."""
    
    def __init__(self):
        """Initialize the MongoDB user repository."""
        self.collection: Optional[AsyncIOMotorCollection] = None
        if mongo_db:
            self.collection = mongo_db.users
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the users collection, ensuring it exists."""
        if not self.collection:
            if not mongo_db:
                raise RuntimeError("MongoDB connection not established")
            self.collection = mongo_db.users
        return self.collection
    
    async def create_user(self, user: User) -> User:
        """Create a new user in the database."""
        try:
            collection = self._get_collection()
            
            # Convert user model to dict for MongoDB
            user_dict = user.model_dump(exclude={"id"})
            
            # Insert user into database
            result = await collection.insert_one(user_dict)
            
            # Update user with the generated ID
            user.id = result.inserted_id
            
            logger.info("Created user with ID: %s, email: %s", user.id, user.email)
            return user
            
        except Exception as e:
            logger.error("Failed to create user: %s", e)
            raise RuntimeError(f"Failed to create user: {e}") from e
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID."""
        try:
            collection = self._get_collection()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            
            # Find user by ID
            user_doc = await collection.find_one({"_id": object_id})
            
            if user_doc:
                # Convert MongoDB document to User model
                user_doc["id"] = user_doc.pop("_id")
                return User(**user_doc)
            
            return None
            
        except Exception as e:
            logger.error("Failed to get user by ID %s: %s", user_id, e)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        try:
            collection = self._get_collection()
            
            # Find user by email
            user_doc = await collection.find_one({"email": email})
            
            if user_doc:
                # Convert MongoDB document to User model
                user_doc["id"] = user_doc.pop("_id")
                return User(**user_doc)
            
            return None
            
        except Exception as e:
            logger.error("Failed to get user by email %s: %s", email, e)
            return None
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Retrieve a user by their Google OAuth ID."""
        try:
            collection = self._get_collection()
            
            # Find user by Google ID
            user_doc = await collection.find_one({"google_id": google_id})
            
            if user_doc:
                # Convert MongoDB document to User model
                user_doc["id"] = user_doc.pop("_id")
                return User(**user_doc)
            
            return None
            
        except Exception as e:
            logger.error("Failed to get user by Google ID %s: %s", google_id, e)
            return None
    
    async def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user information."""
        try:
            collection = self._get_collection()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            
            # Remove None values from updates
            clean_updates = {k: v for k, v in updates.items() if v is not None}
            
            if not clean_updates:
                return await self.get_user_by_id(user_id)
            
            # Update user in database
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": clean_updates}
            )
            
            if result.modified_count > 0:
                logger.info("Updated user with ID: %s", user_id)
                return await self.get_user_by_id(user_id)
            
            return None
            
        except Exception as e:
            logger.error("Failed to update user %s: %s", user_id, e)
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user from the database."""
        try:
            collection = self._get_collection()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            
            # Delete user from database
            result = await collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                logger.info("Deleted user with ID: %s", user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to delete user %s: %s", user_id, e)
            return False
    
    async def add_scan_to_user(self, user_id: str, scan_id: str) -> bool:
        """Add a scan ID to the user's scan history."""
        try:
            collection = self._get_collection()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            scan_object_id = ObjectId(scan_id)
            
            # Add scan ID to user's scan_ids array
            result = await collection.update_one(
                {"_id": object_id},
                {"$addToSet": {"scan_ids": scan_object_id}}
            )
            
            if result.modified_count > 0:
                logger.info("Added scan %s to user %s", scan_id, user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to add scan %s to user %s: %s", scan_id, user_id, e)
            return False
    
    async def update_user_points(self, user_id: str, points: int) -> Optional[User]:
        """Update user's points balance."""
        try:
            collection = self._get_collection()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            
            # Update user points
            result = await collection.update_one(
                {"_id": object_id},
                {"$inc": {"points": points}}
            )
            
            if result.modified_count > 0:
                logger.info("Updated points for user %s: +%d", user_id, points)
                return await self.get_user_by_id(user_id)
            
            return None
            
        except Exception as e:
            logger.error("Failed to update points for user %s: %s", user_id, e)
            return None
    
    async def get_users_by_points_range(self, min_points: int, max_points: int) -> List[User]:
        """Get users within a points range (for leaderboards)."""
        try:
            collection = self._get_collection()
            
            # Find users within points range, sorted by points descending
            cursor = collection.find(
                {"points": {"$gte": min_points, "$lte": max_points}}
            ).sort("points", -1)
            
            users = []
            async for user_doc in cursor:
                # Convert MongoDB document to User model
                user_doc["id"] = user_doc.pop("_id")
                users.append(User(**user_doc))
            
            logger.info("Retrieved %d users in points range %d-%d", len(users), min_points, max_points)
            return users
            
        except Exception as e:
            logger.error("Failed to get users by points range: %s", e)
            return []
