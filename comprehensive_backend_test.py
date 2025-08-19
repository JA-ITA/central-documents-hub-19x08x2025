import requests
import sys
import json
import time
from datetime import datetime
import io

class ComprehensivePolicyRegisterTester:
    def __init__(self, base_url="https://fileaccess-portal-2.preview.emergentagent.com"):
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
        self.unique_id = f"{datetime.now().strftime('%H%M%S')}_{int(time.time() % 10000)}"

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

    def test_admin_authentication(self):
        """Test admin authentication and authorization"""
        print("\n=== AUTHENTICATION & AUTHORIZATION TESTS ===")
        
        # Test admin login
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
            
            # Test getting current user info
            success, response = self.run_test(
                "Get Current User Info",
                "GET",
                "auth/me",
                200
            )
            return True
        return False

    def test_user_management_features(self):
        """Test comprehensive user management features"""
        print("\n=== USER MANAGEMENT FEATURES TESTS ===")
        
        if not self.token:
            self.log_test("User Management Features", False, "No token available")
            return False
        
        # 1. Test user registration
        test_user_data = {
            "username": f"testuser_{self.unique_id}",
            "email": f"test_{self.unique_id}@example.com",
            "full_name": "Test User for Management",
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
            self.test_user_id = response.get('id')
            print(f"   Created test user ID: {self.test_user_id}")
        
        if not self.test_user_id:
            return False
        
        # 2. Test admin user approval process
        success, response = self.run_test(
            "Admin User Approval",
            "PATCH",
            f"users/{self.test_user_id}/approve",
            200
        )
        
        # 3. Test user role changes
        success, response = self.run_test(
            "Change User Role to Policy Manager",
            "PATCH",
            f"users/{self.test_user_id}/role",
            200,
            params={"role": "policy_manager"}
        )
        
        success, response = self.run_test(
            "Change User Role to Admin",
            "PATCH",
            f"users/{self.test_user_id}/role",
            200,
            params={"role": "admin"}
        )
        
        success, response = self.run_test(
            "Change User Role Back to User",
            "PATCH",
            f"users/{self.test_user_id}/role",
            200,
            params={"role": "user"}
        )
        
        # 4. Test user suspension functionality
        success, response = self.run_test(
            "Suspend User",
            "PATCH",
            f"users/{self.test_user_id}/suspend",
            200
        )
        
        # 5. Test user deletion (soft delete)
        success, response = self.run_test(
            "Soft Delete User",
            "DELETE",
            f"users/{self.test_user_id}",
            200
        )
        
        # 6. Test user restoration from suspended/deleted state
        success, response = self.run_test(
            "Restore User from Deleted State",
            "PATCH",
            f"users/{self.test_user_id}/restore",
            200
        )
        
        # 7. Test getting users with different filters
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "users",
            200
        )
        
        success, response = self.run_test(
            "Get Users Including Deleted",
            "GET",
            "users",
            200,
            params={"include_deleted": "true"}
        )
        
        return True

    def test_policy_type_management(self):
        """Test policy type management features"""
        print("\n=== POLICY TYPE MANAGEMENT TESTS ===")
        
        if not self.token:
            self.log_test("Policy Type Management", False, "No token available")
            return False
        
        # 1. Test getting default policy types
        success, response = self.run_test(
            "Get Default Policy Types",
            "GET",
            "policy-types",
            200
        )
        
        if success:
            policy_types = response if isinstance(response, list) else []
            print(f"   Found {len(policy_types)} default policy types")
        
        # 2. Test policy type creation
        custom_type_data = {
            "name": f"Test Custom Type {self.unique_id}",
            "code": f"TCT{self.unique_id[-4:]}",
            "description": "A test custom policy type for comprehensive testing"
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
        
        # 3. Test policy type activation/deactivation
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
        
        # 4. Test policy type listing
        success, response = self.run_test(
            "Get Policy Types Including Inactive",
            "GET",
            "policy-types",
            200,
            params={"include_inactive": "true"}
        )
        
        return True

    def test_category_management_features(self):
        """Test category management features"""
        print("\n=== CATEGORY MANAGEMENT FEATURES TESTS ===")
        
        if not self.token:
            self.log_test("Category Management Features", False, "No token available")
            return False
        
        # 1. Test category creation
        test_category_data = {
            "name": f"Test Category {self.unique_id}",
            "code": f"TC{self.unique_id[-4:]}",
            "description": f"A test category for comprehensive testing {self.unique_id}"
        }
        
        success, response = self.run_test(
            "Create Test Category",
            "POST",
            "categories",
            200,
            data=test_category_data
        )
        
        if success:
            self.test_category_id = response.get('id')
            print(f"   Created test category ID: {self.test_category_id}")
        
        if not self.test_category_id:
            return False
        
        # 2. Test category editing/updating
        update_data = {
            "description": f"Updated test category description {self.unique_id}",
            "is_active": True
        }
        success, response = self.run_test(
            "Update Category",
            "PATCH",
            f"categories/{self.test_category_id}",
            200,
            data=update_data
        )
        
        # 3. Test category deletion (soft delete with is_deleted=true)
        success, response = self.run_test(
            "Soft Delete Category",
            "DELETE",
            f"categories/{self.test_category_id}",
            200
        )
        
        # 4. Test category restoration (is_deleted=false)
        success, response = self.run_test(
            "Restore Category",
            "PATCH",
            f"categories/{self.test_category_id}/restore",
            200
        )
        
        # 5. Test category listing with proper filtering
        success, response = self.run_test(
            "Get Active Categories",
            "GET",
            "categories",
            200
        )
        
        success, response = self.run_test(
            "Get Categories Including Deleted",
            "GET",
            "categories",
            200,
            params={"include_deleted": "true"}
        )
        
        return True

    def test_policy_document_management(self):
        """Test policy document management features"""
        print("\n=== POLICY DOCUMENT MANAGEMENT TESTS ===")
        
        if not self.token:
            self.log_test("Policy Document Management", False, "No token available")
            return False
        
        # First ensure we have a category and policy type
        if not self.test_category_id:
            # Get an existing category
            success, response = self.run_test(
                "Get Categories for Policy Testing",
                "GET",
                "categories",
                200
            )
            if success and response:
                categories = response if isinstance(response, list) else []
                if categories:
                    self.test_category_id = categories[0].get('id')
        
        if not self.test_policy_type_id:
            # Get an existing policy type
            success, response = self.run_test(
                "Get Policy Types for Policy Testing",
                "GET",
                "policy-types",
                200
            )
            if success and response:
                policy_types = response if isinstance(response, list) else []
                if policy_types:
                    self.test_policy_type_id = policy_types[0].get('id')
        
        if not self.test_category_id or not self.test_policy_type_id:
            print("⚠️  Cannot test policy management - missing category or policy type")
            return False
        
        # 1. Test policy upload with file handling
        # Create a simple text file for testing
        test_file_content = f"Test Policy Document Content {self.unique_id}\n\nThis is a test policy document for comprehensive testing."
        
        policy_data = {
            "title": f"Test Policy {self.unique_id}",
            "category_id": self.test_category_id,
            "policy_type_id": self.test_policy_type_id,
            "date_issued": "2025-01-01T00:00:00Z",
            "owner_department": "Test Department",
            "change_summary": "Initial test version"
        }
        
        # Create a file-like object for testing
        files = {
            'file': (f'test_policy_{self.unique_id}.txt', io.StringIO(test_file_content), 'text/plain')
        }
        
        success, response = self.run_test(
            "Upload Policy Document",
            "POST",
            "policies",
            200,
            data=policy_data,
            files=files
        )
        
        # 2. Test getting policies
        success, response = self.run_test(
            "Get All Policies",
            "GET",
            "policies",
            200
        )
        
        if success and response:
            policies = response if isinstance(response, list) else []
            if policies:
                self.test_policy_id = policies[0].get('id')
                print(f"   Using policy ID for testing: {self.test_policy_id}")
        
        if not self.test_policy_id:
            print("⚠️  No policies available for management testing")
            return True  # Not a failure, just no policies to test with
        
        # 3. Test policy visibility toggle (remove from user view using is_visible_to_users)
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
        
        # 4. Test policy deletion (soft delete to status="deleted")
        success, response = self.run_test(
            "Soft Delete Policy",
            "DELETE",
            f"policies/{self.test_policy_id}",
            200
        )
        
        # 5. Test policy restoration from deleted state
        success, response = self.run_test(
            "Restore Policy from Deleted State",
            "PATCH",
            f"policies/{self.test_policy_id}/restore",
            200
        )
        
        # 6. Test policy listing with proper filtering based on user role and visibility
        success, response = self.run_test(
            "Get Policies Including Hidden",
            "GET",
            "policies",
            200,
            params={"include_hidden": "true"}
        )
        
        success, response = self.run_test(
            "Get Policies Including Deleted",
            "GET",
            "policies",
            200,
            params={"include_deleted": "true"}
        )
        
        return True

    def test_authentication_and_authorization(self):
        """Test JWT token authentication and role-based access control"""
        print("\n=== AUTHENTICATION & AUTHORIZATION TESTS ===")
        
        # Test without token (should fail)
        old_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Access Protected Endpoint Without Token",
            "GET",
            "users",
            401  # Should be unauthorized
        )
        
        # Test with invalid token (should fail)
        self.token = "invalid_token"
        
        success, response = self.run_test(
            "Access Protected Endpoint With Invalid Token",
            "GET",
            "users",
            401  # Should be unauthorized
        )
        
        # Restore valid token
        self.token = old_token
        
        # Test admin access to admin-only endpoints
        success, response = self.run_test(
            "Admin Access to User Management",
            "GET",
            "users",
            200
        )
        
        success, response = self.run_test(
            "Admin Access to Policy Type Creation",
            "GET",
            "policy-types",
            200
        )
        
        return True

    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 Starting Comprehensive Policy Management System Backend Tests")
        print("=" * 80)
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code in [200, 404]:
                self.log_test("Basic Connectivity", True, f"Server responding (status: {response.status_code})")
            else:
                self.log_test("Basic Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Basic Connectivity", False, f"Connection failed: {str(e)}")
            return False
        
        # Run all test suites
        if not self.test_admin_authentication():
            print("\n❌ Admin authentication failed. Cannot proceed with authenticated tests.")
            return False
        
        self.test_user_management_features()
        self.test_policy_type_management()
        self.test_category_management_features()
        self.test_policy_document_management()
        self.test_authentication_and_authorization()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 COMPREHENSIVE TEST SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Policy Management System backend is working correctly.")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed")
            
            # Show failed tests
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
            
            return False

def main():
    tester = ComprehensivePolicyRegisterTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())