# Functions to handle all the login scripts, using Google Cloud Datastore. 
# The datastore holds information about the user
import hashlib
import os
import datetime

# OWASP recommended hashing and salting library
# https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#argon2id
import bcrypt

# Google stuff
from google.cloud import datastore, storage
datastore_client = datastore.Client()

def get_salt():
    return bcrypt.gensalt()

def get_hashed_password(pwd, salt):
    return bcrypt.hashpw(pwd.encode('utf-8'), salt)

def create_new_user(username, email, hashed_password, salt):
    user_key = datastore_client.key("UserProfile", username)
    profile = datastore.Entity(key=user_key)
    profile["username"] = username
    profile["email"] = email
    profile["password"] = hashed_password
    profile["salt"] = salt
    datastore_client.put(profile)

def is_unique_username(username):
    query = datastore_client.key("UserProfile", username)
    users = datastore_client.get(query)
    if users:
        # The username already exists
        return False
    else:
        # The username does not exist in the database
        return True

def is_unique_email(email):
    query = datastore_client.key("UserProfile", email)
    users = datastore_client.get(query)
    if users:
        # Email already exists in the system
        return False
    else:
        # Email does not exist and can be used
        return True

def check_password(username, password):
    user_key = datastore_client.key("UserProfile", username)
    user = datastore_client.get(user_key)
    if not user:
        # User not found
        return False
    hash_attempt = get_hashed_password(password, user["salt"])
    if hash_attempt != user["password"]:
        # Hashed password didn't match
        return False
    else:
        return True

def get_signed_url(image_name, data_type):
    storage_client = storage.Client()
    bucket = storage_client.bucket("group3-prof-pics")
    blob_name = image_name
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        # This URL is valid for 15 minutes
        expiration=datetime.timedelta(minutes=15),
        method="PUT",
        content_type= data_type,
    )
    return url

def create_avatar_display_url(self, image_name):
    bucket = self.s.bucket("group3-prof-pics")
    blob = bucket.blob(image_name)

    url = blob.generate_signed_url(
        version="v4",
        # This URL is valid for 15 minutes
        expiration=datetime.timedelta(minutes=15),
        # Allow GET requests using this URL
        method="GET",
        # Note that when content type information is encoded in the blob
        content_type=blob.content_type,
    )
    return url