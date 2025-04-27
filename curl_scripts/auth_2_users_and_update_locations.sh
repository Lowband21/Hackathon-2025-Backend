# 1. Login as User 1 (using the TokenObtainPairView endpoint)
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alexis.perez7@testuser.com", "password": "testpassword"}' \
  -o user1_auth.json

# Store User 1's access token in a variable for easier use
USER1_TOKEN=$(cat user1_auth.json | grep -o '"access":"[^"]*' | grep -o '[^"]*$')

# 2. Login as User 2
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alex.ramirez3@testuser.com", "password": "testpassword"}' \
  -o user2_auth.json

# Store User 2's access token in a variable
USER2_TOKEN=$(cat user2_auth.json | grep -o '"access":"[^"]*' | grep -o '[^"]*$')

# 3. Update User 1's location (Denver, Colorado coordinates)
curl -X POST http://localhost:8000/api/location/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER1_TOKEN" \
  -d '{"latitude": 39.7392, "longitude": -104.9903, "is_active": true}'

# 4. Update User 2's location (within 100m of User 1)
# 100m in latitude is approximately 0.0009 degrees
curl -X POST http://localhost:8000/api/location/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER2_TOKEN" \
  -d '{"latitude": 39.7399, "longitude": -104.9906, "is_active": true}'

# Delete the auth files
rm user1_auth.json
rm user2_auth.json
