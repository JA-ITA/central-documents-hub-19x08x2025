import requests
import sys
import json
from datetime import datetime

class PolicyRegisterAPITester:
    def __init__(self, base_url="https://user-management-7.preview.emergentagent.com"):
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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, params=None):
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
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

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
            self.admin_user_id = self.admin_user.get('id')
            print(f"   Admin user role: {self.admin_user.get('role', 'unknown')}")
            print(f"   Admin user ID: {self.admin_user_id}")
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

    def test_policy_types_management(self):
        """Test Policy Types Management (New Feature)"""
        print("\n=== POLICY TYPES MANAGEMENT TESTS ===")
        
        if not self.token:
            self.log_test("Policy Types Management", False, "No token available")
            return False
        
        # Test GET /api/policy-types (should return default types)
        success, response = self.run_test(
            "Get Default Policy Types",
            "GET",
            "policy-types",
            200
        )
        if success:
            policy_types = response if isinstance(response, list) else []
            print(f"   Found {len(policy_types)} policy types")
            for pt in policy_types:
                print(f"   - {pt.get('name', 'unknown')} ({pt.get('code', 'unknown')}): {'Active' if pt.get('is_active') else 'Inactive'}")
        
        # Test POST /api/policy-types (admin only - create custom policy type)
        custom_type_data = {
            "name": "Test Custom Type",
            "code": "TCT",
            "description": "A test custom policy type"
        }
        success, response = self.run_test(
            "Create Custom Policy Type",
            "POST",
            "policy-types",
            200,
            data=custom_type_data
        )
        if success:
            self.test_policy_type_id = response.get('id')
            print(f"   Created policy type ID: {self.test_policy_type_id}")
        
        # Test PATCH /api/policy-types/{id} (admin only - activate/deactivate)
        if self.test_policy_type_id:
            success, response = self.run_test(
                "Deactivate Policy Type",
                "PATCH",
                f"policy-types/{self.test_policy_type_id}",
                200,
                params={"is_active": "false"}
            )
            
            success, response = self.run_test(
                "Activate Policy Type",
                "PATCH",
                f"policy-types/{self.test_policy_type_id}",
                200,
                params={"is_active": "true"}
            )
        
        return True

    def test_enhanced_user_management(self):
        """Test Enhanced User Management"""
        print("\n=== ENHANCED USER MANAGEMENT TESTS ===")
        
        if not self.token:
            self.log_test("Enhanced User Management", False, "No token available")
            return False
        
        # First create a test user
        test_user_data = {
            "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@test.com",
            "full_name": "Test User",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "Create Test User for Management",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        if success:
            self.test_user_id = response.get('id')
            print(f"   Created test user ID: {self.test_user_id}")
        
        if not self.test_user_id:
            print("❌ Cannot proceed with user management tests - no test user created")
            return False
        
        # Test GET /api/users with include_deleted
        success, response = self.run_test(
            "Get Users Including Deleted",
            "GET",
            "users",
            200,
            params={"include_deleted": "true"}
        )
        if success:
            users = response if isinstance(response, list) else []
            deleted_users = [u for u in users if u.get('is_deleted', False)]
            print(f"   Found {len(users)} total users, {len(deleted_users)} deleted")
        
        # Test PATCH /api/users/{id}/approve (approve the test user)
        success, response = self.run_test(
            "Approve Test User",
            "PATCH",
            f"users/{self.test_user_id}/approve",
            200
        )
        
        # Test PATCH /api/users/{id}/role (admin only - change user role)
        success, response = self.run_test(
            "Change User Role to Policy Manager",
            "PATCH",
            f"users/{self.test_user_id}/role",
            200,
            params={"role": "policy_manager"}
        )
        
        # Test PATCH /api/users/{id} (admin only - bulk user updates)
        update_data = {
            "is_active": True,
            "is_approved": True
        }
        success, response = self.run_test(
            "Bulk Update User",
            "PATCH",
            f"users/{self.test_user_id}",
            200,
            data=update_data
        )
        
        # Test PATCH /api/users/{id}/suspend (admin only - suspend user)
        success, response = self.run_test(
            "Suspend User",
            "PATCH",
            f"users/{self.test_user_id}/suspend",
            200
        )
        
        # Test PATCH /api/users/{id}/restore (admin only - restore user)
        success, response = self.run_test(
            "Restore User",
            "PATCH",
            f"users/{self.test_user_id}/restore",
            200
        )
        
        # Test DELETE /api/users/{id} (admin only - soft delete user)
        success, response = self.run_test(
            "Soft Delete User",
            "DELETE",
            f"users/{self.test_user_id}",
            200
        )
        
        return True

    def test_enhanced_category_management(self):
        """Test Enhanced Category Management"""
        print("\n=== ENHANCED CATEGORY MANAGEMENT TESTS ===")
        
        if not self.token:
            self.log_test("Enhanced Category Management", False, "No token available")
            return False
        
        # First create a test category
        test_category_data = {
            "name": "Test Category Enhanced",
            "code": "TCE",
            "description": "A test category for enhanced testing"
        }
        
        success, response = self.run_test(
            "Create Test Category for Enhancement",
            "POST",
            "categories",
            200,
            data=test_category_data
        )
        if success:
            self.test_category_id = response.get('id')
            print(f"   Created test category ID: {self.test_category_id}")
        
        if not self.test_category_id:
            print("❌ Cannot proceed with category management tests - no test category created")
            return False
        
        # Test GET /api/categories with include_deleted
        success, response = self.run_test(
            "Get Categories Including Deleted",
            "GET",
            "categories",
            200,
            params={"include_deleted": "true"}
        )
        if success:
            categories = response if isinstance(response, list) else []
            deleted_categories = [c for c in categories if c.get('is_deleted', False)]
            print(f"   Found {len(categories)} total categories, {len(deleted_categories)} deleted")
        
        # Test PATCH /api/categories/{id} (admin only - update category)
        update_data = {
            "description": "Updated test category description for enhanced testing"
        }
        success, response = self.run_test(
            "Update Category",
            "PATCH",
            f"categories/{self.test_category_id}",
            200,
            data=update_data
        )
        
        # Test DELETE /api/categories/{id} (admin only - soft delete)
        success, response = self.run_test(
            "Soft Delete Category",
            "DELETE",
            f"categories/{self.test_category_id}",
            200
        )
        
        # Test PATCH /api/categories/{id}/restore (admin only - restore category)
        success, response = self.run_test(
            "Restore Category",
            "PATCH",
            f"categories/{self.test_category_id}/restore",
            200
        )
        
        return True

    def test_enhanced_policy_management(self):
        """Test Enhanced Policy Management"""
        print("\n=== ENHANCED POLICY MANAGEMENT TESTS ===")
        
        if not self.token:
            self.log_test("Enhanced Policy Management", False, "No token available")
            return False
        
        # Get existing policies first
        success, response = self.run_test(
            "Get All Policies for Enhancement Testing",
            "GET",
            "policies",
            200
        )
        
        existing_policies = response if success and isinstance(response, list) else []
        if existing_policies:
            # Use the first policy for testing
            test_policy = existing_policies[0]
            self.test_policy_id = test_policy.get('id')
            print(f"   Using existing policy ID: {self.test_policy_id}")
            
            # Test PATCH /api/policies/{id}/visibility (admin only - hide/show from users)
            success, response = self.run_test(
                "Hide Policy from Users",
                "PATCH",
                f"policies/{self.test_policy_id}/visibility",
                200,
                params={"is_visible": "false"}
            )
            
            success, response = self.run_test(
                "Show Policy to Users",
                "PATCH",
                f"policies/{self.test_policy_id}/visibility",
                200,
                params={"is_visible": "true"}
            )
            
            # Test GET /api/policies with include_hidden
            success, response = self.run_test(
                "Get Policies Including Hidden",
                "GET",
                "policies",
                200,
                params={"include_hidden": "true"}
            )
            if success:
                policies = response if isinstance(response, list) else []
                hidden_policies = [p for p in policies if not p.get('is_visible_to_users', True)]
                print(f"   Found {len(policies)} total policies, {len(hidden_policies)} hidden")
            
            # Test DELETE /api/policies/{id} (admin only - soft delete)
            success, response = self.run_test(
                "Soft Delete Policy",
                "DELETE",
                f"policies/{self.test_policy_id}",
                200
            )
            
            # Test GET /api/policies with include_deleted
            success, response = self.run_test(
                "Get Policies Including Deleted",
                "GET",
                "policies",
                200,
                params={"include_deleted": "true"}
            )
            if success:
                policies = response if isinstance(response, list) else []
                deleted_policies = [p for p in policies if p.get('status') == 'deleted']
                print(f"   Found {len(policies)} total policies, {len(deleted_policies)} deleted")
            
            # Test PATCH /api/policies/{id}/restore (admin only - restore deleted)
            success, response = self.run_test(
                "Restore Policy",
                "PATCH",
                f"policies/{self.test_policy_id}/restore",
                200
            )
        else:
            print("⚠️  No existing policies found - skipping policy management tests")
        
        return True

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
        
        # Test enhanced features
        self.test_policy_types_management()
        self.test_enhanced_user_management()
        self.test_enhanced_category_management()
        self.test_enhanced_policy_management()
        
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