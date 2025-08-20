import requests
import sys
import json
import io
from datetime import datetime
from pathlib import Path

class DocumentRepositoryTester:
    def __init__(self, base_url="https://secure-doc-share.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.user_token = None
        self.admin_user = None
        self.test_user = None
        self.test_user_groups = []
        self.test_documents = []
        self.test_categories = []
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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, params=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        # Use provided token or default admin token
        auth_token = token or self.admin_token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        if not files:
            headers['Content-Type'] = 'application/json'

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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

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

    def setup_authentication(self):
        """Setup admin and user authentication"""
        print("\n=== AUTHENTICATION SETUP ===")
        
        # Admin login
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user = response.get('user', {})
            print(f"   Admin user role: {self.admin_user.get('role', 'unknown')}")
            return True
        return False

    def setup_test_data(self):
        """Setup test data for document repository testing"""
        print("\n=== TEST DATA SETUP ===")
        
        # Create test user groups
        test_groups = [
            {"name": "HR Test Group", "code": "HR_TEST", "description": "HR test group for document access"},
            {"name": "IT Test Group", "code": "IT_TEST", "description": "IT test group for document access"},
            {"name": "Finance Test Group", "code": "FIN_TEST", "description": "Finance test group for document access"}
        ]
        
        for group_data in test_groups:
            success, response = self.run_test(
                f"Create User Group: {group_data['name']}",
                "POST",
                "user-groups",
                200,
                data=group_data
            )
            if success:
                self.test_user_groups.append(response)
        
        # Create test user
        unique_id = f"{datetime.now().strftime('%H%M%S')}"
        test_user_data = {
            "username": f"doctest_{unique_id}",
            "email": f"doctest_{unique_id}@test.com",
            "full_name": "Document Test User",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "Create Test User",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success:
            self.test_user = response
            # Approve the test user
            self.run_test(
                "Approve Test User",
                "PATCH",
                f"users/{self.test_user['id']}/approve",
                200
            )
            
            # Assign user to test groups
            group_ids = [group['id'] for group in self.test_user_groups[:2]]  # Assign to first 2 groups
            self.run_test(
                "Assign User to Groups",
                "PATCH",
                f"users/{self.test_user['id']}/groups",
                200,
                data=group_ids
            )
        
        # Get existing categories for testing
        success, response = self.run_test(
            "Get Categories for Testing",
            "GET",
            "categories",
            200
        )
        if success:
            self.test_categories = response
        
        return len(self.test_user_groups) > 0 and self.test_user is not None

    def test_document_upload_and_visibility(self):
        """Test document upload with default visibility settings"""
        print("\n=== DOCUMENT UPLOAD AND VISIBILITY TESTS ===")
        
        if not self.test_categories:
            print("❌ No categories available for testing")
            return False
        
        category_id = self.test_categories[0]['id']
        
        # Test different document types
        document_types = ["policy", "memo", "document", "procedure", "guideline", "notice"]
        
        for doc_type in document_types:
            # Create test file content
            test_content = f"This is a test {doc_type} document for visibility testing.\nCreated at: {datetime.now()}"
            test_file = io.BytesIO(test_content.encode())
            
            # Upload document
            form_data = {
                "title": f"Test {doc_type.title()} Document",
                "document_type": doc_type,
                "category_id": category_id,
                "date_issued": datetime.now().isoformat(),
                "owner_department": "Test Department",
                "description": f"Test {doc_type} for visibility testing",
                "tags": f"test,{doc_type},visibility"
            }
            
            files = {"file": (f"test_{doc_type}.txt", test_file, "text/plain")}
            
            success, response = self.run_test(
                f"Upload {doc_type.title()} Document",
                "POST",
                "documents",
                200,
                data=form_data,
                files=files
            )
            
            if success:
                document = response.get('document', {})
                self.test_documents.append(document)
                
                # Verify default visibility settings
                is_visible_to_users = document.get('is_visible_to_users', False)
                visible_to_groups = document.get('visible_to_groups', [])
                status = document.get('status', '')
                
                if is_visible_to_users and status == 'active':
                    self.log_test(f"Default Visibility Check - {doc_type.title()}", True, 
                                f"Document has correct default visibility (public: {is_visible_to_users}, status: {status})")
                else:
                    self.log_test(f"Default Visibility Check - {doc_type.title()}", False, 
                                f"Document has incorrect default visibility (public: {is_visible_to_users}, status: {status})")
        
        return True

    def test_document_immediate_visibility(self):
        """Test that uploaded documents appear immediately"""
        print("\n=== DOCUMENT IMMEDIATE VISIBILITY TESTS ===")
        
        # Test admin API visibility
        success, response = self.run_test(
            "Check Admin Documents List",
            "GET",
            "documents",
            200
        )
        
        if success:
            admin_docs = response if isinstance(response, list) else []
            uploaded_doc_ids = [doc.get('id') for doc in self.test_documents]
            visible_in_admin = [doc for doc in admin_docs if doc.get('id') in uploaded_doc_ids]
            
            self.log_test("Admin API Document Visibility", len(visible_in_admin) == len(self.test_documents),
                        f"Found {len(visible_in_admin)}/{len(self.test_documents)} uploaded documents in admin API")
        
        # Test public API visibility
        success, response = self.run_test(
            "Check Public Documents List",
            "GET",
            "public/documents",
            200,
            token=""  # No authentication for public API
        )
        
        if success:
            public_docs = response if isinstance(response, list) else []
            uploaded_doc_ids = [doc.get('id') for doc in self.test_documents]
            visible_in_public = [doc for doc in public_docs if doc.get('id') in uploaded_doc_ids]
            
            self.log_test("Public API Document Visibility", len(visible_in_public) == len(self.test_documents),
                        f"Found {len(visible_in_public)}/{len(self.test_documents)} uploaded documents in public API")
        
        return True

    def test_group_based_access_controls(self):
        """Test group-based access controls"""
        print("\n=== GROUP-BASED ACCESS CONTROLS TESTS ===")
        
        if not self.test_documents or not self.test_user_groups:
            print("❌ No test documents or groups available")
            return False
        
        # Test document visibility controls with groups
        test_doc = self.test_documents[0]
        doc_id = test_doc.get('id')
        
        if not doc_id:
            print("❌ No valid document ID for testing")
            return False
        
        # Test setting document to group-only visibility
        group_ids = [self.test_user_groups[0]['id']]  # Restrict to first test group
        visibility_data = {
            "is_visible_to_users": False,  # Hide from public
            "visible_to_groups": group_ids  # Only visible to specific group
        }
        
        success, response = self.run_test(
            "Set Document Group-Only Visibility",
            "PATCH",
            f"documents/{doc_id}/visibility",
            200,
            data=visibility_data
        )
        
        if success:
            # Verify document is hidden from public API
            success, response = self.run_test(
                "Verify Document Hidden from Public",
                "GET",
                f"public/documents/{doc_id}",
                404,
                token=""  # No authentication
            )
            
            # Verify document is still visible in admin API
            success, response = self.run_test(
                "Verify Document Visible to Admin",
                "GET",
                f"documents/{doc_id}",
                200
            )
            
            # Test setting document back to public visibility
            visibility_data = {
                "is_visible_to_users": True,
                "visible_to_groups": []
            }
            
            success, response = self.run_test(
                "Restore Document Public Visibility",
                "PATCH",
                f"documents/{doc_id}/visibility",
                200,
                data=visibility_data
            )
            
            if success:
                # Verify document is visible in public API again
                success, response = self.run_test(
                    "Verify Document Restored to Public",
                    "GET",
                    f"public/documents/{doc_id}",
                    200,
                    token=""  # No authentication
                )
        
        return True

    def test_user_group_management(self):
        """Test user group management CRUD operations"""
        print("\n=== USER GROUP MANAGEMENT TESTS ===")
        
        # Test listing user groups
        success, response = self.run_test(
            "List User Groups",
            "GET",
            "user-groups",
            200
        )
        
        if success:
            groups = response if isinstance(response, list) else []
            print(f"   Found {len(groups)} user groups")
        
        # Test updating a user group
        if self.test_user_groups:
            test_group = self.test_user_groups[0]
            group_id = test_group['id']
            
            update_data = {
                "description": f"Updated description for {test_group['name']} - {datetime.now()}"
            }
            
            success, response = self.run_test(
                "Update User Group",
                "PUT",
                f"user-groups/{group_id}",
                200,
                data=update_data
            )
            
            # Test soft delete user group
            success, response = self.run_test(
                "Delete User Group",
                "DELETE",
                f"user-groups/{group_id}",
                200
            )
            
            # Test restore user group
            success, response = self.run_test(
                "Restore User Group",
                "PATCH",
                f"user-groups/{group_id}/restore",
                200
            )
        
        return True

    def test_admin_interface_backend_support(self):
        """Test admin interface backend support"""
        print("\n=== ADMIN INTERFACE BACKEND SUPPORT TESTS ===")
        
        if not self.test_documents:
            print("❌ No test documents available")
            return False
        
        test_doc = self.test_documents[0]
        doc_id = test_doc.get('id')
        
        # Test PATCH /api/documents/{id}/visibility with both parameters
        visibility_combinations = [
            {"is_visible_to_users": True, "visible_to_groups": []},
            {"is_visible_to_users": False, "visible_to_groups": [self.test_user_groups[0]['id']] if self.test_user_groups else []},
            {"is_visible_to_users": True, "visible_to_groups": [group['id'] for group in self.test_user_groups[:2]]},
            {"is_visible_to_users": False, "visible_to_groups": []}
        ]
        
        for i, visibility_data in enumerate(visibility_combinations):
            success, response = self.run_test(
                f"Admin Visibility Control Test {i+1}",
                "PATCH",
                f"documents/{doc_id}/visibility",
                200,
                data=visibility_data
            )
            
            if success:
                # Verify the changes took effect
                success, response = self.run_test(
                    f"Verify Visibility Changes {i+1}",
                    "GET",
                    f"documents/{doc_id}",
                    200
                )
                
                if success:
                    doc_data = response
                    actual_public = doc_data.get('is_visible_to_users', False)
                    actual_groups = doc_data.get('visible_to_groups', [])
                    expected_public = visibility_data['is_visible_to_users']
                    expected_groups = visibility_data['visible_to_groups']
                    
                    if actual_public == expected_public and set(actual_groups) == set(expected_groups):
                        self.log_test(f"Visibility Verification {i+1}", True, 
                                    f"Visibility settings applied correctly")
                    else:
                        self.log_test(f"Visibility Verification {i+1}", False, 
                                    f"Expected public:{expected_public}, groups:{expected_groups}. Got public:{actual_public}, groups:{actual_groups}")
        
        # Test document filtering for different user roles
        success, response = self.run_test(
            "Admin Document Filtering - Show All",
            "GET",
            "documents",
            200,
            params={"show_hidden": "true", "show_deleted": "false"}
        )
        
        if success:
            all_docs = response if isinstance(response, list) else []
            print(f"   Admin can see {len(all_docs)} documents (including hidden)")
        
        # Test document soft delete and restore
        success, response = self.run_test(
            "Soft Delete Document",
            "DELETE",
            f"documents/{doc_id}",
            200
        )
        
        if success:
            # Verify document is hidden from public API
            success, response = self.run_test(
                "Verify Deleted Document Hidden from Public",
                "GET",
                f"public/documents/{doc_id}",
                404,
                token=""
            )
            
            # Restore document
            success, response = self.run_test(
                "Restore Document",
                "PATCH",
                f"documents/{doc_id}/restore",
                200
            )
        
        return True

    def test_document_access_by_user_groups(self):
        """Test document access based on user group membership"""
        print("\n=== DOCUMENT ACCESS BY USER GROUPS TESTS ===")
        
        if not self.test_user or not self.test_documents or not self.test_user_groups:
            print("❌ Missing test data for group access testing")
            return False
        
        # Login as test user
        success, response = self.run_test(
            "Test User Login",
            "POST",
            "auth/login",
            200,
            data={"username": self.test_user['username'], "password": "testpass123"}
        )
        
        if not success:
            print("❌ Could not login as test user")
            return False
        
        user_token = response.get('access_token')
        
        # Test document access with user token
        test_doc = self.test_documents[0]
        doc_id = test_doc.get('id')
        
        # First, set document to group-only visibility (user should have access)
        group_ids = [self.test_user_groups[0]['id']]  # User is assigned to this group
        visibility_data = {
            "is_visible_to_users": False,
            "visible_to_groups": group_ids
        }
        
        success, response = self.run_test(
            "Set Document to User's Group Only",
            "PATCH",
            f"documents/{doc_id}/visibility",
            200,
            data=visibility_data
        )
        
        if success:
            # Test user can access document through their group membership
            success, response = self.run_test(
                "User Access Document via Group Membership",
                "GET",
                f"documents/{doc_id}",
                200,
                token=user_token
            )
            
            # Set document to different group (user should not have access)
            other_group_ids = [self.test_user_groups[2]['id']]  # User is not assigned to this group
            visibility_data = {
                "is_visible_to_users": False,
                "visible_to_groups": other_group_ids
            }
            
            success, response = self.run_test(
                "Set Document to Different Group",
                "PATCH",
                f"documents/{doc_id}/visibility",
                200,
                data=visibility_data
            )
            
            if success:
                # Test user cannot access document (not in the group)
                success, response = self.run_test(
                    "User Cannot Access Document (Wrong Group)",
                    "GET",
                    f"documents/{doc_id}",
                    404,
                    token=user_token
                )
        
        return True

    def run_comprehensive_tests(self):
        """Run all document repository tests"""
        print("🚀 Starting Document Repository Comprehensive Tests")
        print("=" * 70)
        
        # Setup authentication
        if not self.setup_authentication():
            print("\n❌ Authentication setup failed. Cannot proceed.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Test data setup failed. Cannot proceed.")
            return False
        
        # Run all test suites
        self.test_document_upload_and_visibility()
        self.test_document_immediate_visibility()
        self.test_group_based_access_controls()
        self.test_user_group_management()
        self.test_admin_interface_backend_support()
        self.test_document_access_by_user_groups()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All document repository tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['message']}")
            
            return False

def main():
    tester = DocumentRepositoryTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())