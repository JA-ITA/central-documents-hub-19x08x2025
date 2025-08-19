#!/usr/bin/env python3
"""
Focused test for admin login functionality and public policy access
Based on review request requirements:
1. Test POST /api/auth/login with admin credentials (username: admin, password: admin123)
2. Verify the response includes access_token and user data
3. Test that the token works for authenticated endpoints like GET /api/policies
4. Test the new test policy document exists in GET /api/public/policies
5. Test that the PDF file can be downloaded from GET /api/public/policies/{id}/download for the test policy
"""

import requests
import sys
import json
import os
from datetime import datetime

class AdminLoginTester:
    def __init__(self):
        # Use the backend URL from frontend/.env
        self.base_url = "https://repo-navigator-11.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.admin_user = None
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

    def make_request(self, method, endpoint, data=None, params=None, use_auth=True):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None

    def test_1_admin_login(self):
        """Test 1: Admin login with credentials (username: admin, password: admin123)"""
        print("\n🔍 Test 1: Testing admin login...")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.make_request('POST', 'auth/login', data=login_data, use_auth=False)
        
        if not response:
            self.log_test("Admin Login", False, "Request failed")
            return False
        
        if response.status_code != 200:
            self.log_test("Admin Login", False, f"Expected status 200, got {response.status_code}. Response: {response.text}")
            return False
        
        try:
            response_data = response.json()
        except:
            self.log_test("Admin Login", False, "Invalid JSON response")
            return False
        
        # Check if response includes access_token and user data
        if 'access_token' not in response_data:
            self.log_test("Admin Login", False, "Response missing access_token")
            return False
        
        if 'user' not in response_data:
            self.log_test("Admin Login", False, "Response missing user data")
            return False
        
        # Store token and user data for subsequent tests
        self.token = response_data['access_token']
        self.admin_user = response_data['user']
        
        # Verify user data structure
        user_data = response_data['user']
        required_fields = ['id', 'username', 'role', 'email', 'full_name']
        missing_fields = [field for field in required_fields if field not in user_data]
        
        if missing_fields:
            self.log_test("Admin Login", False, f"User data missing fields: {missing_fields}")
            return False
        
        # Verify admin role
        if user_data.get('role') != 'admin':
            self.log_test("Admin Login", False, f"Expected admin role, got {user_data.get('role')}")
            return False
        
        self.log_test("Admin Login", True, f"Successfully logged in as admin user: {user_data.get('username')}")
        print(f"   Token type: {response_data.get('token_type', 'bearer')}")
        print(f"   User ID: {user_data.get('id')}")
        print(f"   User role: {user_data.get('role')}")
        print(f"   User email: {user_data.get('email')}")
        
        return True

    def test_2_authenticated_endpoint(self):
        """Test 2: Test that the token works for authenticated endpoints like GET /api/policies"""
        print("\n🔍 Test 2: Testing authenticated endpoint access...")
        
        if not self.token:
            self.log_test("Authenticated Endpoint Access", False, "No token available from login test")
            return False
        
        response = self.make_request('GET', 'policies')
        
        if not response:
            self.log_test("Authenticated Endpoint Access", False, "Request failed")
            return False
        
        if response.status_code != 200:
            self.log_test("Authenticated Endpoint Access", False, f"Expected status 200, got {response.status_code}. Response: {response.text}")
            return False
        
        try:
            policies = response.json()
        except:
            self.log_test("Authenticated Endpoint Access", False, "Invalid JSON response")
            return False
        
        if not isinstance(policies, list):
            self.log_test("Authenticated Endpoint Access", False, "Expected list of policies")
            return False
        
        self.log_test("Authenticated Endpoint Access", True, f"Successfully accessed policies endpoint, found {len(policies)} policies")
        
        # Store first policy ID for later tests if available
        if policies:
            self.test_policy_id = policies[0].get('id')
            print(f"   Sample policy: {policies[0].get('title', 'Unknown')} (ID: {self.test_policy_id})")
        
        return True

    def test_3_public_policies_endpoint(self):
        """Test 3: Test the new test policy document exists in GET /api/public/policies"""
        print("\n🔍 Test 3: Testing public policies endpoint...")
        
        response = self.make_request('GET', 'public/policies', use_auth=False)
        
        if not response:
            self.log_test("Public Policies Access", False, "Request failed")
            return False
        
        if response.status_code != 200:
            self.log_test("Public Policies Access", False, f"Expected status 200, got {response.status_code}. Response: {response.text}")
            return False
        
        try:
            public_policies = response.json()
        except:
            self.log_test("Public Policies Access", False, "Invalid JSON response")
            return False
        
        if not isinstance(public_policies, list):
            self.log_test("Public Policies Access", False, "Expected list of policies")
            return False
        
        # Check if we have any visible policies
        visible_policies = [p for p in public_policies if p.get('is_visible_to_users', False)]
        active_policies = [p for p in public_policies if p.get('status') in ['active', 'archived']]
        
        self.log_test("Public Policies Access", True, f"Successfully accessed public policies, found {len(public_policies)} total policies")
        print(f"   Visible to users: {len(visible_policies)}")
        print(f"   Active/Archived: {len(active_policies)}")
        
        # Store a test policy ID for download test
        if public_policies:
            self.test_policy_id = public_policies[0].get('id')
            test_policy = public_policies[0]
            print(f"   Test policy for download: {test_policy.get('title', 'Unknown')} (ID: {self.test_policy_id})")
            print(f"   Policy status: {test_policy.get('status')}")
            print(f"   Visible to users: {test_policy.get('is_visible_to_users')}")
        
        return True

    def test_4_create_test_policy_if_needed(self):
        """Test 4: Create a test policy if none exists for download testing"""
        print("\n🔍 Test 4: Ensuring test policy exists for download testing...")
        
        if not self.token:
            self.log_test("Test Policy Creation", False, "No admin token available")
            return False
        
        # Check if we already have a policy from previous test
        if self.test_policy_id:
            self.log_test("Test Policy Creation", True, f"Using existing policy ID: {self.test_policy_id}")
            return True
        
        # Get categories and policy types first
        categories_response = self.make_request('GET', 'categories')
        policy_types_response = self.make_request('GET', 'policy-types')
        
        if not categories_response or categories_response.status_code != 200:
            self.log_test("Test Policy Creation", False, "Cannot get categories")
            return False
        
        if not policy_types_response or policy_types_response.status_code != 200:
            self.log_test("Test Policy Creation", False, "Cannot get policy types")
            return False
        
        try:
            categories = categories_response.json()
            policy_types = policy_types_response.json()
        except:
            self.log_test("Test Policy Creation", False, "Invalid JSON in categories or policy types")
            return False
        
        if not categories or not policy_types:
            self.log_test("Test Policy Creation", False, "No categories or policy types available")
            return False
        
        # Create a simple text file to upload as test document
        test_content = """TEST POLICY DOCUMENT

This is a test policy document created for API testing purposes.

Policy Title: Test Policy for Download Testing
Created: {datetime.now().isoformat()}
Purpose: Verify PDF download functionality

This document contains test content to verify that the policy management system
can properly handle document uploads and downloads.

END OF TEST DOCUMENT"""
        
        test_file_path = "/tmp/test_policy.txt"
        try:
            with open(test_file_path, 'w') as f:
                f.write(test_content)
        except Exception as e:
            self.log_test("Test Policy Creation", False, f"Cannot create test file: {str(e)}")
            return False
        
        # Prepare form data for policy creation
        form_data = {
            'title': 'Test Policy for Download Testing',
            'category_id': categories[0]['id'],
            'policy_type_id': policy_types[0]['id'],
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department',
            'change_summary': 'Initial test policy creation'
        }
        
        # Upload policy with file
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_policy.txt', f, 'text/plain')}
                headers = {'Authorization': f'Bearer {self.token}'}
                
                response = requests.post(
                    f"{self.api_url}/policies",
                    data=form_data,
                    files=files,
                    headers=headers,
                    timeout=30
                )
        except Exception as e:
            self.log_test("Test Policy Creation", False, f"Upload request failed: {str(e)}")
            return False
        finally:
            # Clean up test file
            try:
                os.remove(test_file_path)
            except:
                pass
        
        if response.status_code not in [200, 201]:
            self.log_test("Test Policy Creation", False, f"Upload failed with status {response.status_code}: {response.text}")
            return False
        
        try:
            upload_result = response.json()
            policy_number = upload_result.get('policy_number')
            
            # Get the created policy to find its ID
            policies_response = self.make_request('GET', 'policies')
            if policies_response and policies_response.status_code == 200:
                policies = policies_response.json()
                for policy in policies:
                    if policy.get('policy_number') == policy_number:
                        self.test_policy_id = policy.get('id')
                        break
            
            self.log_test("Test Policy Creation", True, f"Created test policy: {policy_number} (ID: {self.test_policy_id})")
            return True
            
        except Exception as e:
            self.log_test("Test Policy Creation", False, f"Failed to parse upload response: {str(e)}")
            return False

    def test_5_public_policy_download(self):
        """Test 5: Test that the PDF file can be downloaded from GET /api/public/policies/{id}/download"""
        print("\n🔍 Test 5: Testing public policy download...")
        
        if not self.test_policy_id:
            self.log_test("Public Policy Download", False, "No test policy ID available")
            return False
        
        # First, make sure the policy is visible to public
        if self.token:
            visibility_response = self.make_request(
                'PATCH', 
                f'policies/{self.test_policy_id}/visibility',
                params={'is_visible': 'true'}
            )
            if visibility_response and visibility_response.status_code == 200:
                print(f"   Ensured policy {self.test_policy_id} is visible to public")
        
        # Test the download endpoint
        response = self.make_request('GET', f'public/policies/{self.test_policy_id}/download', use_auth=False)
        
        if not response:
            self.log_test("Public Policy Download", False, "Download request failed")
            return False
        
        if response.status_code != 200:
            self.log_test("Public Policy Download", False, f"Expected status 200, got {response.status_code}. Response: {response.text}")
            return False
        
        # Check response headers for file download
        content_type = response.headers.get('content-type', '')
        content_disposition = response.headers.get('content-disposition', '')
        content_length = response.headers.get('content-length', '0')
        
        # Check if we got file content
        if len(response.content) == 0:
            self.log_test("Public Policy Download", False, "Downloaded file is empty")
            return False
        
        self.log_test("Public Policy Download", True, f"Successfully downloaded policy document ({content_length} bytes)")
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Disposition: {content_disposition}")
        print(f"   File size: {len(response.content)} bytes")
        
        return True

    def test_6_additional_public_endpoints(self):
        """Test 6: Test additional public endpoints for completeness"""
        print("\n🔍 Test 6: Testing additional public endpoints...")
        
        # Test public categories
        response = self.make_request('GET', 'public/categories', use_auth=False)
        if response and response.status_code == 200:
            try:
                categories = response.json()
                self.log_test("Public Categories", True, f"Found {len(categories)} public categories")
            except:
                self.log_test("Public Categories", False, "Invalid JSON response")
        else:
            self.log_test("Public Categories", False, f"Failed with status {response.status_code if response else 'No response'}")
        
        # Test public policy types
        response = self.make_request('GET', 'public/policy-types', use_auth=False)
        if response and response.status_code == 200:
            try:
                policy_types = response.json()
                self.log_test("Public Policy Types", True, f"Found {len(policy_types)} public policy types")
            except:
                self.log_test("Public Policy Types", False, "Invalid JSON response")
        else:
            self.log_test("Public Policy Types", False, f"Failed with status {response.status_code if response else 'No response'}")
        
        # Test public policy detail
        if self.test_policy_id:
            response = self.make_request('GET', f'public/policies/{self.test_policy_id}', use_auth=False)
            if response and response.status_code == 200:
                try:
                    policy = response.json()
                    self.log_test("Public Policy Detail", True, f"Retrieved policy: {policy.get('title', 'Unknown')}")
                except:
                    self.log_test("Public Policy Detail", False, "Invalid JSON response")
            else:
                self.log_test("Public Policy Detail", False, f"Failed with status {response.status_code if response else 'No response'}")
        
        return True

    def run_all_tests(self):
        """Run all admin login and public access tests"""
        print("🚀 Starting Admin Login and Public Policy Access Tests")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 70)
        
        # Run tests in sequence
        test_methods = [
            self.test_1_admin_login,
            self.test_2_authenticated_endpoint,
            self.test_3_public_policies_endpoint,
            self.test_4_create_test_policy_if_needed,
            self.test_5_public_policy_download,
            self.test_6_additional_public_endpoints
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All admin login and public access tests passed!")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} test(s) failed")
            
            # Show failed tests
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
            
            return False

def main():
    """Main function to run the tests"""
    tester = AdminLoginTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())