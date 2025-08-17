#!/usr/bin/env python3

import jwt
from bson import ObjectId

# Test token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGExN2Q1MWJmMmI1NzUwNmMwMWZiMjIiLCJlbWFpbCI6ImFycWlsYXNwQGdtYWlsLmNvbSIsIm5hbWUiOiJBcnFpbGEgU3VyeWEgUHV0cmEiLCJleHAiOjE3NTYwMjQ4MTZ9.MHn47eWmT8lkOpWjIP3SPGvJYi-ItdaGy_mknYemf3U"

# Decode token
JWT_SECRET_KEY = "551265b057390be3973f3acaf86341483e6cf87ff804da221071c806a8097054"
payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])

print("Token payload:", payload)
print("User ID (sub):", payload["sub"])
print("User ID type:", type(payload["sub"]))

# Test ObjectId conversion
try:
    user_id = ObjectId(payload["sub"])
    print("Converted ObjectId:", user_id)
    print("ObjectId type:", type(user_id))
except Exception as e:
    print("Error converting to ObjectId:", e)
