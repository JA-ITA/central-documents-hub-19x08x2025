import requests
import sys
import json
import io
from datetime import datetime

class EdgeCaseDocumentTester:
    def __init__(self, base_url="https://secure-doc-share.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, message=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED - {message}")
        else:
            print(f"❌ {name}: FAILED - {message}")

    def setup_auth(self):
        """Setup admin authentication"""
        response = requests.post(f"{self.api_url}/auth/login", 
                               json={"username": "admin", "password": "admin123"})
        if response.status_code == 200:
            self.admin_token = response.json()['access_token']
            return True
        return False

    def test_document_visibility_edge_cases(self):
        """Test edge cases for document visibility"""
        print("\n=== DOCUMENT VISIBILITY EDGE CASES ===")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test public API with various filters
        test_cases = [
            ("Empty search", {"search": ""}),
            ("Non-existent category", {"category_id": "non-existent-id"}),
            ("Invalid document type", {"document_type": "invalid_type"}),
            ("Multiple filters", {"search": "test", "document_type": "policy"}),
        ]
        
        for test_name, params in test_cases:
            response = requests.get(f"{self.api_url}/public/documents", params=params)
            success = response.status_code == 200
            self.log_test(f"Public API - {test_name}", success, 
                         f"Status: {response.status_code}")
        
        # Test document access with invalid IDs
        invalid_ids = ["invalid-id", "00000000-0000-0000-0000-000000000000", ""]
        
        for invalid_id in invalid_ids:
            if invalid_id:  # Skip empty string for URL construction
                response = requests.get(f"{self.api_url}/public/documents/{invalid_id}")
                success = response.status_code == 404
                self.log_test(f"Invalid Document ID Access - {invalid_id[:10]}...", success,
                             f"Correctly returned 404 for invalid ID")

    def test_group_assignment_edge_cases(self):
        """Test edge cases for group assignments"""
        print("\n=== GROUP ASSIGNMENT EDGE CASES ===")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get a test user
        response = requests.get(f"{self.api_url}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            test_users = [u for u in users if u.get('role') != 'admin' and not u.get('is_deleted')]
            
            if test_users:
                user_id = test_users[0]['id']
                
                # Test assigning non-existent groups
                response = requests.patch(f"{self.api_url}/users/{user_id}/groups",
                                        json=["non-existent-group-id"], headers=headers)
                success = response.status_code == 404
                self.log_test("Assign Non-existent Group", success,
                             f"Correctly rejected non-existent group")
                
                # Test assigning empty group list
                response = requests.patch(f"{self.api_url}/users/{user_id}/groups",
                                        json=[], headers=headers)
                success = response.status_code == 200
                self.log_test("Assign Empty Group List", success,
                             f"Successfully cleared user groups")

    def test_document_upload_edge_cases(self):
        """Test edge cases for document uploads"""
        print("\n=== DOCUMENT UPLOAD EDGE CASES ===")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get categories for testing
        response = requests.get(f"{self.api_url}/categories", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            if categories:
                category_id = categories[0]['id']
                
                # Test upload with missing required fields
                test_file = io.BytesIO(b"Test content")
                files = {"file": ("test.txt", test_file, "text/plain")}
                
                incomplete_data = {
                    "title": "Test Document",
                    # Missing required fields
                }
                
                response = requests.post(f"{self.api_url}/documents", 
                                       data=incomplete_data, files=files, headers=headers)
                success = response.status_code == 422  # Validation error expected
                self.log_test("Upload with Missing Fields", success,
                             f"Correctly rejected incomplete data")
                
                # Test upload with invalid category
                test_file = io.BytesIO(b"Test content")
                files = {"file": ("test.txt", test_file, "text/plain")}
                
                invalid_data = {
                    "title": "Test Document",
                    "document_type": "document",
                    "category_id": "invalid-category-id",
                    "date_issued": datetime.now().isoformat(),
                    "owner_department": "Test Department"
                }
                
                response = requests.post(f"{self.api_url}/documents", 
                                       data=invalid_data, files=files, headers=headers)
                success = response.status_code == 404  # Category not found
                self.log_test("Upload with Invalid Category", success,
                             f"Correctly rejected invalid category")

    def test_public_api_security(self):
        """Test public API security and access controls"""
        print("\n=== PUBLIC API SECURITY TESTS ===")
        
        # Test public endpoints without authentication
        public_endpoints = [
            "/public/documents",
            "/public/categories", 
            "/public/policy-types"
        ]
        
        for endpoint in public_endpoints:
            response = requests.get(f"{self.api_url}{endpoint}")
            success = response.status_code == 200
            self.log_test(f"Public Access - {endpoint}", success,
                         f"Public endpoint accessible without auth")
        
        # Test that admin endpoints require authentication
        admin_endpoints = [
            "/documents",
            "/users",
            "/user-groups"
        ]
        
        for endpoint in admin_endpoints:
            response = requests.get(f"{self.api_url}{endpoint}")
            success = response.status_code == 401  # Unauthorized expected
            self.log_test(f"Admin Endpoint Security - {endpoint}", success,
                         f"Correctly requires authentication")

    def test_document_download_edge_cases(self):
        """Test document download edge cases"""
        print("\n=== DOCUMENT DOWNLOAD EDGE CASES ===")
        
        # Test downloading non-existent document
        response = requests.get(f"{self.api_url}/public/documents/non-existent-id/download")
        success = response.status_code == 404
        self.log_test("Download Non-existent Document", success,
                     f"Correctly returned 404 for non-existent document")
        
        # Test downloading without proper permissions
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get a document and make it group-only
        response = requests.get(f"{self.api_url}/documents", headers=headers)
        if response.status_code == 200:
            documents = response.json()
            if documents:
                doc_id = documents[0]['id']
                
                # Make document group-only
                visibility_data = {
                    "is_visible_to_users": False,
                    "visible_to_groups": ["some-group-id"]
                }
                requests.patch(f"{self.api_url}/documents/{doc_id}/visibility",
                             json=visibility_data, headers=headers)
                
                # Try to download via public API (should fail)
                response = requests.get(f"{self.api_url}/public/documents/{doc_id}/download")
                success = response.status_code == 404
                self.log_test("Download Group-Only Document via Public API", success,
                             f"Correctly blocked access to group-only document")

    def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("🔍 Starting Document Repository Edge Case Tests")
        print("=" * 60)
        
        if not self.setup_auth():
            print("❌ Authentication failed")
            return False
        
        self.test_document_visibility_edge_cases()
        self.test_group_assignment_edge_cases()
        self.test_document_upload_edge_cases()
        self.test_public_api_security()
        self.test_document_download_edge_cases()
        
        print("\n" + "=" * 60)
        print(f"📊 Edge Case Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = EdgeCaseDocumentTester()
    success = tester.run_edge_case_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())