#!/usr/bin/env python3

import jwt
import datetime

# JWT secret from .env
JWT_SECRET_KEY = "551265b057390be3973f3acaf86341483e6cf87ff804da221071c806a8097054"
JWT_ALGORITHM = "HS256"

# User data from database - using correct ObjectId
user_data = {
    "sub": "68a17d51bf2b57506c01fb22",  # ObjectId from MongoDB
    "email": "arqilasp@gmail.com",
    "name": "Arqila Surya Putra",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10080)
}

# Generate token
token = jwt.encode(user_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
print(f"Bearer {token}")
