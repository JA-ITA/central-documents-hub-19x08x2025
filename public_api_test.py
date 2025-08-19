import requests
import sys
import json
from datetime import datetime
import time

class PublicAPITester:
    def __init__(self, base_url="https://repo-navigator-11.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_policy_id = None
        self.test_category_id = None
        self.test_policy_type_id = None
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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, params=None, use_auth=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Only add auth header if explicitly requested
        if use_auth and self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'
        
        if files:
            # Remove Content-Type for file uploads
            headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Auth: {'Yes' if use_auth and self.admin_token else 'No'}")
        
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

    def setup_admin_auth(self):
        """Get admin token for setup operations"""
        print("\n=== ADMIN SETUP FOR PUBLIC API TESTING ===")
        
        success, response = self.run_test(
            "Admin Login for Setup",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained successfully")
            return True
        return False

    def setup_test_data(self):
        """Create test data for public API testing"""
        print("\n=== SETTING UP TEST DATA ===")
        
        if not self.admin_token:
            print("❌ No admin token available for setup")
            return False

        # Get existing categories and policy types
        success, categories = self.run_test(
            "Get Categories for Setup",
            "GET",
            "categories",
            200,
            use_auth=True
        )
        
        success, policy_types = self.run_test(
            "Get Policy Types for Setup",
            "GET",
            "policy-types",
            200,
            use_auth=True
        )
        
        if not categories or not policy_types:
            print("❌ Cannot get categories or policy types for setup")
            return False

        # Use first available category and policy type
        self.test_category_id = categories[0]['id'] if categories else None
        self.test_policy_type_id = policy_types[0]['id'] if policy_types else None
        
        print(f"   Using category ID: {self.test_category_id}")
        print(f"   Using policy type ID: {self.test_policy_type_id}")

        # Check if we have any existing visible policies
        success, existing_policies = self.run_test(
            "Check Existing Visible Policies",
            "GET",
            "public/policies",
            200
        )
        
        if success and existing_policies:
            print(f"   Found {len(existing_policies)} existing visible policies")
            self.test_policy_id = existing_policies[0]['id']
            return True

        # Create a test policy if none exist
        print("   No visible policies found, creating test policy...")
        
        # Create a simple text file to upload as policy document
        test_content = f"""
TEST POLICY DOCUMENT
Created: {datetime.now().isoformat()}
This is a test policy document for public API testing.
"""
        
        # Create test policy using form data
        policy_data = {
            'title': 'Test Public Policy',
            'category_id': self.test_category_id,
            'policy_type_id': self.test_policy_type_id,
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department',
            'change_summary': 'Initial test policy creation'
        }
        
        # Create a temporary file-like object
        files = {
            'file': ('test_policy.pdf', test_content.encode(), 'application/pdf')
        }
        
        success, response = self.run_test(
            "Create Test Policy",
            "POST",
            "policies",
            200,
            data=policy_data,
            files=files,
            use_auth=True
        )
        
        if success:
            # Get the created policy ID by fetching policies
            success, policies = self.run_test(
                "Get Created Policy ID",
                "GET",
                "policies",
                200,
                use_auth=True
            )
            
            if success and policies:
                # Find our test policy
                for policy in policies:
                    if policy.get('title') == 'Test Public Policy':
                        self.test_policy_id = policy['id']
                        print(f"   Created test policy ID: {self.test_policy_id}")
                        
                        # Make sure it's visible to users
                        success, response = self.run_test(
                            "Make Test Policy Visible",
                            "PATCH",
                            f"policies/{self.test_policy_id}/visibility",
                            200,
                            params={"is_visible": "true"},
                            use_auth=True
                        )
                        
                        return True
        
        print("❌ Failed to create test policy")
        return False

    def test_public_policies_endpoint(self):
        """Test GET /api/public/policies endpoint"""
        print("\n=== TESTING PUBLIC POLICIES ENDPOINT ===")
        
        # Test basic retrieval
        success, response = self.run_test(
            "Get All Public Policies",
            "GET",
            "public/policies",
            200
        )
        
        if success:
            policies = response if isinstance(response, list) else []
            print(f"   Found {len(policies)} public policies")
            
            # Verify all policies are visible and have correct status
            for policy in policies:
                if not policy.get('is_visible_to_users', False):
                    self.log_test("Policy Visibility Check", False, f"Policy {policy.get('id')} is not visible to users")
                    return False
                if policy.get('status') not in ['active', 'archived']:
                    self.log_test("Policy Status Check", False, f"Policy {policy.get('id')} has invalid status: {policy.get('status')}")
                    return False
            
            self.log_test("Policy Visibility and Status Check", True, "All policies are properly visible and have valid status")

        # Test search functionality
        success, response = self.run_test(
            "Search Public Policies",
            "GET",
            "public/policies",
            200,
            params={"search": "test"}
        )
        
        if success:
            search_results = response if isinstance(response, list) else []
            print(f"   Search returned {len(search_results)} results")

        # Test category filtering
        if self.test_category_id:
            success, response = self.run_test(
                "Filter Policies by Category",
                "GET",
                "public/policies",
                200,
                params={"category_id": self.test_category_id}
            )
            
            if success:
                filtered_results = response if isinstance(response, list) else []
                print(f"   Category filter returned {len(filtered_results)} results")

        # Test status filtering
        success, response = self.run_test(
            "Filter Policies by Active Status",
            "GET",
            "public/policies",
            200,
            params={"status": "active"}
        )
        
        if success:
            active_policies = response if isinstance(response, list) else []
            print(f"   Active status filter returned {len(active_policies)} results")

        success, response = self.run_test(
            "Filter Policies by Archived Status",
            "GET",
            "public/policies",
            200,
            params={"status": "archived"}
        )
        
        if success:
            archived_policies = response if isinstance(response, list) else []
            print(f"   Archived status filter returned {len(archived_policies)} results")

        return True

    def test_public_single_policy_endpoint(self):
        """Test GET /api/public/policies/{policy_id} endpoint"""
        print("\n=== TESTING PUBLIC SINGLE POLICY ENDPOINT ===")
        
        if not self.test_policy_id:
            self.log_test("Single Policy Test", False, "No test policy ID available")
            return False

        # Test retrieving a visible policy
        success, response = self.run_test(
            "Get Single Public Policy",
            "GET",
            f"public/policies/{self.test_policy_id}",
            200
        )
        
        if success:
            policy = response
            print(f"   Retrieved policy: {policy.get('title', 'unknown')}")
            print(f"   Policy status: {policy.get('status', 'unknown')}")
            print(f"   Visible to users: {policy.get('is_visible_to_users', 'unknown')}")

        # Test accessing non-existent policy
        fake_policy_id = "non-existent-policy-id"
        success, response = self.run_test(
            "Get Non-existent Policy (Should 404)",
            "GET",
            f"public/policies/{fake_policy_id}",
            404
        )

        # Test accessing hidden policy (first hide it, then try to access)
        if self.test_policy_id and self.admin_token:
            # Hide the policy
            success, response = self.run_test(
                "Hide Test Policy",
                "PATCH",
                f"policies/{self.test_policy_id}/visibility",
                200,
                params={"is_visible": "false"},
                use_auth=True
            )
            
            if success:
                # Try to access hidden policy via public endpoint
                success, response = self.run_test(
                    "Access Hidden Policy (Should 404)",
                    "GET",
                    f"public/policies/{self.test_policy_id}",
                    404
                )
                
                # Restore visibility for other tests
                success, response = self.run_test(
                    "Restore Policy Visibility",
                    "PATCH",
                    f"policies/{self.test_policy_id}/visibility",
                    200,
                    params={"is_visible": "true"},
                    use_auth=True
                )

        return True

    def test_public_policy_download_endpoint(self):
        """Test GET /api/public/policies/{policy_id}/download endpoint"""
        print("\n=== TESTING PUBLIC POLICY DOWNLOAD ENDPOINT ===")
        
        if not self.test_policy_id:
            self.log_test("Policy Download Test", False, "No test policy ID available")
            return False

        # Test downloading a visible policy
        success, response = self.run_test(
            "Download Public Policy",
            "GET",
            f"public/policies/{self.test_policy_id}/download",
            200
        )
        
        if success:
            print(f"   Download successful, response type: {type(response)}")

        # Test downloading non-existent policy
        fake_policy_id = "non-existent-policy-id"
        success, response = self.run_test(
            "Download Non-existent Policy (Should 404)",
            "GET",
            f"public/policies/{fake_policy_id}/download",
            404
        )

        # Test downloading hidden policy
        if self.test_policy_id and self.admin_token:
            # Hide the policy
            success, response = self.run_test(
                "Hide Policy for Download Test",
                "PATCH",
                f"policies/{self.test_policy_id}/visibility",
                200,
                params={"is_visible": "false"},
                use_auth=True
            )
            
            if success:
                # Try to download hidden policy
                success, response = self.run_test(
                    "Download Hidden Policy (Should 404)",
                    "GET",
                    f"public/policies/{self.test_policy_id}/download",
                    404
                )
                
                # Restore visibility
                success, response = self.run_test(
                    "Restore Policy Visibility for Download",
                    "PATCH",
                    f"policies/{self.test_policy_id}/visibility",
                    200,
                    params={"is_visible": "true"},
                    use_auth=True
                )

        return True

    def test_public_categories_endpoint(self):
        """Test GET /api/public/categories endpoint"""
        print("\n=== TESTING PUBLIC CATEGORIES ENDPOINT ===")
        
        # Test retrieving active categories
        success, response = self.run_test(
            "Get Public Categories",
            "GET",
            "public/categories",
            200
        )
        
        if success:
            categories = response if isinstance(response, list) else []
            print(f"   Found {len(categories)} public categories")
            
            # Verify all categories are active and not deleted
            for category in categories:
                if category.get('is_deleted', False):
                    self.log_test("Category Deleted Check", False, f"Category {category.get('id')} is deleted but returned")
                    return False
                if not category.get('is_active', False):
                    self.log_test("Category Active Check", False, f"Category {category.get('id')} is inactive but returned")
                    return False
            
            self.log_test("Category Status Check", True, "All categories are properly active and not deleted")
            
            # Print category details
            for cat in categories:
                print(f"   - {cat.get('name', 'unknown')} ({cat.get('code', 'unknown')})")

        return True

    def test_public_policy_types_endpoint(self):
        """Test GET /api/public/policy-types endpoint"""
        print("\n=== TESTING PUBLIC POLICY TYPES ENDPOINT ===")
        
        # Test retrieving active policy types
        success, response = self.run_test(
            "Get Public Policy Types",
            "GET",
            "public/policy-types",
            200
        )
        
        if success:
            policy_types = response if isinstance(response, list) else []
            print(f"   Found {len(policy_types)} public policy types")
            
            # Verify all policy types are active and not deleted
            for policy_type in policy_types:
                if policy_type.get('is_deleted', False):
                    self.log_test("Policy Type Deleted Check", False, f"Policy type {policy_type.get('id')} is deleted but returned")
                    return False
                if not policy_type.get('is_active', False):
                    self.log_test("Policy Type Active Check", False, f"Policy type {policy_type.get('id')} is inactive but returned")
                    return False
            
            self.log_test("Policy Type Status Check", True, "All policy types are properly active and not deleted")
            
            # Print policy type details
            for pt in policy_types:
                print(f"   - {pt.get('name', 'unknown')} ({pt.get('code', 'unknown')})")

        return True

    def test_authentication_not_required(self):
        """Test that public endpoints don't require authentication"""
        print("\n=== TESTING NO AUTHENTICATION REQUIRED ===")
        
        # Test all public endpoints without any authorization headers
        endpoints_to_test = [
            ("public/policies", "Public Policies"),
            ("public/categories", "Public Categories"),
            ("public/policy-types", "Public Policy Types")
        ]
        
        if self.test_policy_id:
            endpoints_to_test.extend([
                (f"public/policies/{self.test_policy_id}", "Single Public Policy"),
                (f"public/policies/{self.test_policy_id}/download", "Public Policy Download")
            ])
        
        for endpoint, name in endpoints_to_test:
            # Make request without any authentication
            url = f"{self.api_url}/{endpoint}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    self.log_test(f"No Auth Required - {name}", True, f"Endpoint accessible without authentication")
                else:
                    self.log_test(f"No Auth Required - {name}", False, f"Expected 200, got {response.status_code}")
            except Exception as e:
                self.log_test(f"No Auth Required - {name}", False, f"Exception: {str(e)}")

        return True

    def run_all_tests(self):
        """Run all public API tests"""
        print("🚀 Starting Public API Endpoint Tests")
        print("=" * 60)
        
        # Setup admin authentication for test data creation
        if not self.setup_admin_auth():
            print("\n❌ Cannot get admin authentication. Stopping tests.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Cannot setup test data. Stopping tests.")
            return False
        
        # Run public API tests
        self.test_authentication_not_required()
        self.test_public_policies_endpoint()
        self.test_public_single_policy_endpoint()
        self.test_public_policy_download_endpoint()
        self.test_public_categories_endpoint()
        self.test_public_policy_types_endpoint()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All public API tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = PublicAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())