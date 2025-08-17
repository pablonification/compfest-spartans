#!/usr/bin/env python3
"""
Test MongoDB Atlas connection
"""
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Replace with your actual MongoDB Atlas password
uri = "mongodb+srv://athianbintang:<db_password>@smartbin.nvapx6z.mongodb.net/?retryWrites=true&w=majority&appName=smartbin"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("✅ Pinged your deployment. You successfully connected to MongoDB Atlas!")
    
    # List databases
    print("📊 Available databases:")
    for db_name in client.list_database_names():
        print(f"   - {db_name}")
        
    # Test smartbin database
    db = client['smartbin']
    print(f"\n📁 Collections in 'smartbin' database:")
    collections = db.list_collection_names()
    if collections:
        for coll_name in collections:
            print(f"   - {coll_name}")
    else:
        print("   (No collections found)")
        
except Exception as e:
    print(f"❌ Connection failed: {e}")
finally:
    client.close()
