import requests
import sys
import json
from datetime import datetime

class PolicyRegisterAPITester:
    def __init__(self, base_url="https://1a2700c4-f211-433b-868e-21d0913b895c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_user = None
        self.admin_user_id = None
        self.test_user_id = None
        self.test_category_id = None
        self.test_policy_type_id = None
        self.test_policy_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, message="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED - {message}")
        else:
            print(f"❌ {name}: FAILED - {message}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "message": message,
            "response_data": response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            # Remove Content-Type for file uploads
            headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
                return True, response_data
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}. Response: {response_data}")
                return False, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code in [200, 404]:  # 404 is fine, means server is running
                self.log_test("Basic Connectivity", True, f"Server responding (status: {response.status_code})")
                return True
            else:
                self.log_test("Basic Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Basic Connectivity", False, f"Connection failed: {str(e)}")
            return False

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user = response.get('user', {})
            print(f"   Admin user role: {self.admin_user.get('role', 'unknown')}")
            return True
        return False

    def test_auth_me(self):
        """Test getting current user info"""
        if not self.token:
            self.log_test("Get Current User", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_user_registration(self):
        """Test user registration"""
        test_user_data = {
            "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "full_name": "Test User",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success:
            print(f"   Registered user: {response.get('username', 'unknown')}")
            print(f"   Approval status: {response.get('is_approved', 'unknown')}")
        
        return success

    def test_get_categories(self):
        """Test getting categories"""
        if not self.token:
            self.log_test("Get Categories", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if success:
            categories = response if isinstance(response, list) else []
            print(f"   Found {len(categories)} categories")
            for cat in categories:
                print(f"   - {cat.get('name', 'unknown')} ({cat.get('code', 'unknown')})")
        
        return success

    def test_create_category(self):
        """Test creating a new category"""
        if not self.token:
            self.log_test("Create Category", False, "No token available")
            return False
            
        test_category = {
            "name": "Test Category",
            "code": "TEST",
            "description": "Test category for API testing"
        }
        
        success, response = self.run_test(
            "Create Category",
            "POST",
            "categories",
            200,
            data=test_category
        )
        
        if success:
            print(f"   Created category: {response.get('name', 'unknown')}")
        
        return success

    def test_get_policies(self):
        """Test getting policies"""
        if not self.token:
            self.log_test("Get Policies", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get Policies",
            "GET",
            "policies",
            200
        )
        
        if success:
            policies = response if isinstance(response, list) else []
            print(f"   Found {len(policies)} policies")
            for policy in policies:
                print(f"   - {policy.get('title', 'unknown')} ({policy.get('policy_number', 'unknown')})")
        
        return success

    def test_get_users_admin(self):
        """Test getting users (admin only)"""
        if not self.token:
            self.log_test("Get Users (Admin)", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get Users (Admin)",
            "GET",
            "users",
            200
        )
        
        if success:
            users = response if isinstance(response, list) else []
            print(f"   Found {len(users)} users")
            for user in users:
                print(f"   - {user.get('username', 'unknown')} ({user.get('role', 'unknown')}) - Approved: {user.get('is_approved', 'unknown')}")
        
        return success

    def test_file_upload_structure(self):
        """Test policy creation endpoint structure (without actual file)"""
        if not self.token:
            self.log_test("Policy Upload Structure", False, "No token available")
            return False
            
        # Test with missing file to check endpoint structure
        success, response = self.run_test(
            "Policy Upload Structure",
            "POST",
            "policies",
            422,  # Expecting validation error due to missing file
            data={
                "title": "Test Policy",
                "category_id": "test-id",
                "policy_type": "policy",
                "date_issued": "2025-01-01",
                "owner_department": "Test Department"
            }
        )
        
        # 422 is expected for missing file, so we consider this a pass if we get validation error
        if not success and response and "detail" in str(response):
            self.log_test("Policy Upload Structure", True, "Endpoint exists and validates input correctly")
            return True
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Central Policy Register Backend API Tests")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_basic_connectivity():
            print("\n❌ Cannot connect to server. Stopping tests.")
            return False
        
        # Test authentication
        if not self.test_admin_login():
            print("\n❌ Admin login failed. Cannot proceed with authenticated tests.")
            return False
        
        # Test authenticated endpoints
        self.test_auth_me()
        self.test_user_registration()
        self.test_get_categories()
        self.test_create_category()
        self.test_get_policies()
        self.test_get_users_admin()
        self.test_file_upload_structure()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = PolicyRegisterAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())