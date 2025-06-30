#!/usr/bin/env python3
"""
Test script for authentication system
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import (
    hash_password, verify_password, create_access_token, verify_token,
    create_guest_session, get_guest_session, init_auth_db, create_user,
    get_user_by_username, authenticate_user
)

async def test_auth_system():
    """Test the authentication system"""
    print("🧪 Testing Authentication System")
    print("=" * 50)
    
    # Test password hashing
    print("1. Testing password hashing...")
    password = "testpassword123"
    hashed = hash_password(password)
    print(f"   Original password: {password}")
    print(f"   Hashed password: {hashed[:20]}...")
    
    # Test password verification
    print("2. Testing password verification...")
    is_valid = verify_password(password, hashed)
    print(f"   Password verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    is_invalid = verify_password("wrongpassword", hashed)
    print(f"   Wrong password verification: {'✅ PASS' if not is_invalid else '❌ FAIL'}")
    
    # Test JWT token creation and verification
    print("3. Testing JWT tokens...")
    user_data = {"sub": "test_user_id", "username": "testuser"}
    token = create_access_token(user_data)
    print(f"   Created token: {token[:20]}...")
    
    try:
        payload = verify_token(token)
        print(f"   Token verification: ✅ PASS")
        print(f"   Token payload: {payload}")
    except Exception as e:
        print(f"   Token verification: ❌ FAIL - {e}")
    
    # Test guest session
    print("4. Testing guest sessions...")
    guest_session = create_guest_session()
    print(f"   Created guest session: {guest_session.session_id[:20]}...")
    print(f"   Session expires at: {guest_session.expires_at}")
    
    retrieved_session = get_guest_session(guest_session.session_id)
    print(f"   Session retrieval: {'✅ PASS' if retrieved_session else '❌ FAIL'}")
    
    # Test database operations
    print("5. Testing database operations...")
    try:
        await init_auth_db()
        print("   Database initialization: ✅ PASS")
        
        # Test user creation
        user_id = await create_user("testuser", "testpass123", "test@example.com")
        print(f"   User creation: ✅ PASS (ID: {user_id})")
        
        # Test user retrieval
        user = await get_user_by_username("testuser")
        if user:
            print(f"   User retrieval: ✅ PASS (Username: {user['username']})")
        else:
            print("   User retrieval: ❌ FAIL")
        
        # Test authentication
        auth_user = await authenticate_user("testuser", "testpass123")
        if auth_user:
            print(f"   User authentication: ✅ PASS (Username: {auth_user['username']})")
        else:
            print("   User authentication: ❌ FAIL")
        
        # Test wrong password
        wrong_auth = await authenticate_user("testuser", "wrongpass")
        print(f"   Wrong password auth: {'✅ PASS' if not wrong_auth else '❌ FAIL'}")
        
    except Exception as e:
        print(f"   Database operations: ❌ FAIL - {e}")
    
    print("\n" + "=" * 50)
    print("✅ Authentication system test completed!")

if __name__ == "__main__":
    asyncio.run(test_auth_system()) 