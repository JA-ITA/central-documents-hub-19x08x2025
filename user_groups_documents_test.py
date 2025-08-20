import requests
import sys
import json
import io
from datetime import datetime
from pathlib import Path

class UserGroupsDocumentsAPITester:
    def __init__(self, base_url="https://secure-doc-share.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_user = None
        self.test_user_id = None
        self.test_user_groups = []
        self.test_documents = []
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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, params=None, json_data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if not files and not json_data:
            headers['Content-Type'] = 'application/json'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                elif json_data:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=json_data, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'PATCH':
                if json_data:
                    response = requests.patch(url, json=json_data, headers=headers)
                else:
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

    def test_admin_login(self):
        """Test admin login with provided credentials"""
        print("\n=== ADMIN AUTHENTICATION ===")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            json_data={"username": "admin", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_user = response.get('user', {})
            print(f"   Admin user role: {self.admin_user.get('role', 'unknown')}")
            print(f"   Admin user ID: {self.admin_user.get('id')}")
            return True
        return False

    def test_user_group_management(self):
        """Test Priority 1: User Group Management (Admin endpoints)"""
        print("\n=== PRIORITY 1: USER GROUP MANAGEMENT ===")
        
        if not self.token:
            self.log_test("User Group Management", False, "No admin token available")
            return False

        # Test creating HR user group
        hr_group_data = {
            "name": "HR Department",
            "code": "HR_TEST",
            "description": "Human Resources Department for testing",
            "department": "Human Resources"
        }
        
        success, response = self.run_test(
            "Create HR User Group",
            "POST",
            "user-groups",
            200,
            json_data=hr_group_data
        )
        
        if success:
            hr_group_id = response.get('id')
            self.test_user_groups.append({"id": hr_group_id, "name": "HR_TEST", "data": response})
            print(f"   Created HR group ID: {hr_group_id}")

        # Test creating IT user group
        it_group_data = {
            "name": "IT Department",
            "code": "IT_TEST",
            "description": "Information Technology Department for testing",
            "department": "Information Technology"
        }
        
        success, response = self.run_test(
            "Create IT User Group",
            "POST",
            "user-groups",
            200,
            json_data=it_group_data
        )
        
        if success:
            it_group_id = response.get('id')
            self.test_user_groups.append({"id": it_group_id, "name": "IT_TEST", "data": response})
            print(f"   Created IT group ID: {it_group_id}")

        # Test creating Finance user group
        finance_group_data = {
            "name": "Finance Department",
            "code": "FIN_TEST",
            "description": "Finance and Accounting Department for testing",
            "department": "Finance"
        }
        
        success, response = self.run_test(
            "Create Finance User Group",
            "POST",
            "user-groups",
            200,
            json_data=finance_group_data
        )
        
        if success:
            finance_group_id = response.get('id')
            self.test_user_groups.append({"id": finance_group_id, "name": "FIN_TEST", "data": response})
            print(f"   Created Finance group ID: {finance_group_id}")

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
            for group in groups:
                print(f"   - {group.get('name', 'unknown')} ({group.get('code', 'unknown')})")

        # Test updating a user group (if we have one)
        if self.test_user_groups:
            test_group = self.test_user_groups[0]
            update_data = {
                "description": "Updated description for testing purposes"
            }
            
            success, response = self.run_test(
                "Update User Group",
                "PUT",
                f"user-groups/{test_group['id']}",
                200,
                data=update_data
            )

        # Test deleting and restoring user groups
        if self.test_user_groups:
            test_group = self.test_user_groups[0]
            
            # Delete user group
            success, response = self.run_test(
                "Delete User Group",
                "DELETE",
                f"user-groups/{test_group['id']}",
                200
            )
            
            # Restore user group
            success, response = self.run_test(
                "Restore User Group",
                "PATCH",
                f"user-groups/{test_group['id']}/restore",
                200
            )

        return True

    def create_test_document_file(self, filename="test_document.txt", content="This is a test document for API testing."):
        """Create a test document file in memory"""
        return io.BytesIO(content.encode('utf-8'))

    def test_document_management(self):
        """Test Priority 2: Document Management"""
        print("\n=== PRIORITY 2: DOCUMENT MANAGEMENT ===")
        
        if not self.token:
            self.log_test("Document Management", False, "No admin token available")
            return False

        # First, get available categories and policy types
        success, categories = self.run_test(
            "Get Categories for Document Testing",
            "GET",
            "categories",
            200
        )
        
        if not success or not categories:
            print("   ⚠️  No categories available for document testing")
            return False

        category_id = categories[0].get('id') if categories else None
        
        success, policy_types = self.run_test(
            "Get Policy Types for Document Testing",
            "GET",
            "policy-types",
            200
        )
        
        policy_type_id = policy_types[0].get('id') if success and policy_types else None

        # Test uploading different document types
        document_types = [
            {"type": "policy", "title": "Test Policy Document"},
            {"type": "memo", "title": "Test Memo Document"},
            {"type": "document", "title": "Test General Document"}
        ]

        for doc_type in document_types:
            # Create test file
            test_file = self.create_test_document_file(
                f"test_{doc_type['type']}.txt",
                f"This is a test {doc_type['type']} document content."
            )
            
            # Prepare form data
            form_data = {
                "title": doc_type['title'],
                "document_type": doc_type['type'],
                "category_id": category_id,
                "date_issued": datetime.now().isoformat(),
                "owner_department": "Test Department",
                "description": f"Test {doc_type['type']} for API testing"
            }
            
            if policy_type_id and doc_type['type'] == 'policy':
                form_data["policy_type_id"] = policy_type_id

            files = {"file": (f"test_{doc_type['type']}.txt", test_file, "text/plain")}
            
            success, response = self.run_test(
                f"Upload {doc_type['type'].title()} Document",
                "POST",
                "documents",
                200,
                data=form_data,
                files=files
            )
            
            if success:
                document_id = response.get('document', {}).get('id')
                if document_id:
                    self.test_documents.append({
                        "id": document_id,
                        "type": doc_type['type'],
                        "title": doc_type['title']
                    })
                    print(f"   Created {doc_type['type']} document ID: {document_id}")

        # Test listing documents with filtering
        success, response = self.run_test(
            "List All Documents",
            "GET",
            "documents",
            200
        )
        
        if success:
            documents = response if isinstance(response, list) else []
            print(f"   Found {len(documents)} documents")

        # Test filtering by document type
        success, response = self.run_test(
            "Filter Documents by Type (Policy)",
            "GET",
            "documents",
            200,
            params={"document_type": "policy"}
        )

        # Test document visibility settings
        if self.test_documents and self.test_user_groups:
            test_doc = self.test_documents[0]
            test_group = self.test_user_groups[0]
            
            # Update document visibility to specific groups
            visibility_data = {
                "is_visible_to_users": False,
                "visible_to_groups": [test_group['id']]
            }
            
            success, response = self.run_test(
                "Update Document Visibility (Group-specific)",
                "PATCH",
                f"documents/{test_doc['id']}/visibility",
                200,
                json_data=visibility_data
            )
            
            # Test making document public again
            visibility_data = {
                "is_visible_to_users": True,
                "visible_to_groups": []
            }
            
            success, response = self.run_test(
                "Update Document Visibility (Public)",
                "PATCH",
                f"documents/{test_doc['id']}/visibility",
                200,
                json_data=visibility_data
            )

        return True

    def test_user_group_assignment(self):
        """Test Priority 3: User Group Assignment"""
        print("\n=== PRIORITY 3: USER GROUP ASSIGNMENT ===")
        
        if not self.token:
            self.log_test("User Group Assignment", False, "No admin token available")
            return False

        # First, create a test user or get existing users
        success, users = self.run_test(
            "Get Users for Group Assignment",
            "GET",
            "users",
            200
        )
        
        if success and users:
            # Find a non-admin user to test with
            test_users = [u for u in users if u.get('role') != 'admin' and not u.get('is_deleted', False)]
            if test_users:
                self.test_user_id = test_users[0].get('id')
                print(f"   Using user ID for testing: {self.test_user_id}")
            else:
                # Create a test user
                unique_id = datetime.now().strftime('%H%M%S')
                test_user_data = {
                    "username": f"grouptest_{unique_id}",
                    "email": f"grouptest_{unique_id}@test.com",
                    "full_name": "Group Test User",
                    "password": "testpass123"
                }
                
                success, response = self.run_test(
                    "Create Test User for Group Assignment",
                    "POST",
                    "auth/register",
                    200,
                    json_data=test_user_data
                )
                
                if success:
                    self.test_user_id = response.get('id')
                    print(f"   Created test user ID: {self.test_user_id}")

        if not self.test_user_id:
            print("   ⚠️  No test user available for group assignment")
            return False

        # Test assigning user to groups
        if self.test_user_groups:
            group_ids = [group['id'] for group in self.test_user_groups[:2]]  # Assign to first 2 groups
            
            success, response = self.run_test(
                "Assign User to Groups",
                "PATCH",
                f"users/{self.test_user_id}/groups",
                200,
                json_data=group_ids
            )
            
            if success:
                print(f"   Assigned user to {len(group_ids)} groups")

        return True

    def test_public_document_api(self):
        """Test Priority 4: Public Document API"""
        print("\n=== PRIORITY 4: PUBLIC DOCUMENT API ===")
        
        # Test public documents endpoint (no authentication required)
        success, response = self.run_test(
            "Get Public Documents (No Auth)",
            "GET",
            "public/documents",
            200
        )
        
        if success:
            documents = response if isinstance(response, list) else []
            print(f"   Found {len(documents)} public documents")
            
            # Test downloading a public document if available
            if documents:
                test_doc = documents[0]
                doc_id = test_doc.get('id')
                
                success, response = self.run_test(
                    "Get Public Document Details",
                    "GET",
                    f"public/documents/{doc_id}",
                    200
                )
                
                # Test downloading public document
                success, response = self.run_test(
                    "Download Public Document",
                    "GET",
                    f"public/documents/{doc_id}/download",
                    200
                )
                
                if success:
                    print(f"   Successfully downloaded document (size: {len(str(response))} bytes)")

        return True

    def test_document_access_controls(self):
        """Test document access controls based on user groups"""
        print("\n=== DOCUMENT ACCESS CONTROLS TESTING ===")
        
        if not self.token or not self.test_documents or not self.test_user_groups:
            print("   ⚠️  Insufficient test data for access control testing")
            return False

        # Test setting document visibility to specific groups
        if self.test_documents and self.test_user_groups:
            test_doc = self.test_documents[0]
            test_group = self.test_user_groups[0]
            
            # Make document visible only to specific group
            visibility_data = {
                "is_visible_to_users": False,
                "visible_to_groups": [test_group['id']]
            }
            
            success, response = self.run_test(
                "Set Document Group-Only Visibility",
                "PATCH",
                f"documents/{test_doc['id']}/visibility",
                200,
                json_data=visibility_data
            )
            
            # Verify document is not in public API
            success, response = self.run_test(
                "Verify Document Not in Public API",
                "GET",
                "public/documents",
                200
            )
            
            if success:
                public_docs = response if isinstance(response, list) else []
                doc_ids = [doc.get('id') for doc in public_docs]
                if test_doc['id'] not in doc_ids:
                    self.log_test("Document Access Control", True, "Document correctly hidden from public API")
                else:
                    self.log_test("Document Access Control", False, "Document still visible in public API")

        return True

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== CLEANUP TEST DATA ===")
        
        if not self.token:
            return

        # Delete test documents
        for doc in self.test_documents:
            success, response = self.run_test(
                f"Delete Test Document ({doc['title']})",
                "DELETE",
                f"documents/{doc['id']}",
                200
            )

        # Delete test user groups
        for group in self.test_user_groups:
            success, response = self.run_test(
                f"Delete Test User Group ({group['name']})",
                "DELETE",
                f"user-groups/{group['id']}",
                200
            )

    def run_all_tests(self):
        """Run all user groups and documents tests"""
        print("🚀 Starting User Groups and Documents Backend API Tests")
        print("=" * 70)
        
        # Test admin authentication
        if not self.test_admin_login():
            print("\n❌ Admin login failed. Cannot proceed with tests.")
            return False
        
        # Run priority tests
        self.test_user_group_management()
        self.test_document_management()
        self.test_user_group_assignment()
        self.test_public_document_api()
        self.test_document_access_controls()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed")
            
            # Show failed tests
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['message']}")
            
            return False

def main():
    tester = UserGroupsDocumentsAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())