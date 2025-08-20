#!/usr/bin/env python3
"""
Document Defaults and Edge Cases Test
====================================
This test specifically checks default values and edge cases for document visibility.
"""

import requests
import sys
import json
import io
from datetime import datetime

class DocumentDefaultsTester:
    def __init__(self, base_url="https://secure-doc-share.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.test_category_id = None
        self.test_policy_type_id = None
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

    def setup_auth_and_data(self):
        """Setup authentication and get test data"""
        # Login as admin
        response = requests.post(f"{self.api_url}/auth/login", 
                               json={"username": "admin", "password": "admin123"})
        if response.status_code == 200:
            self.token = response.json()['access_token']
            print("✅ Admin authentication successful")
        else:
            print("❌ Admin authentication failed")
            return False
        
        # Get categories
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{self.api_url}/categories", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            if categories:
                self.test_category_id = categories[0]['id']
                print(f"✅ Using category: {categories[0]['name']}")
        
        # Get policy types
        response = requests.get(f"{self.api_url}/policy-types", headers=headers)
        if response.status_code == 200:
            policy_types = response.json()
            if policy_types:
                self.test_policy_type_id = policy_types[0]['id']
                print(f"✅ Using policy type: {policy_types[0]['name']}")
        
        return self.test_category_id and self.test_policy_type_id

    def test_policy_default_values(self):
        """Test that policies get correct default values"""
        print("\n🔍 Testing Policy Default Values...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create minimal policy upload
        test_file = io.BytesIO(b"Test policy content")
        form_data = {
            'title': 'Default Values Test Policy',
            'category_id': self.test_category_id,
            'policy_type_id': self.test_policy_type_id,
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department'
            # Note: NOT setting is_visible_to_users or status explicitly
        }
        
        files = {'file': ('test.pdf', test_file, 'application/pdf')}
        
        response = requests.post(f"{self.api_url}/policies", 
                               data=form_data, files=files, headers=headers)
        
        if response.status_code == 200:
            policy_number = response.json().get('policy_number')
            print(f"   Created policy: {policy_number}")
            
            # Now get the policy to check its default values
            response = requests.get(f"{self.api_url}/policies", 
                                  headers=headers, 
                                  params={"include_hidden": "true", "include_deleted": "true"})
            
            if response.status_code == 200:
                policies = response.json()
                created_policy = None
                for policy in policies:
                    if policy.get('policy_number') == policy_number:
                        created_policy = policy
                        break
                
                if created_policy:
                    is_visible = created_policy.get('is_visible_to_users')
                    status = created_policy.get('status')
                    
                    print(f"   Default is_visible_to_users: {is_visible}")
                    print(f"   Default status: {status}")
                    
                    # Check if defaults are correct
                    if is_visible is True and status == 'active':
                        self.log_test("Policy Default Values", True, 
                                    f"is_visible_to_users={is_visible}, status={status}")
                        return True
                    else:
                        self.log_test("Policy Default Values", False, 
                                    f"Expected is_visible_to_users=True and status='active', got is_visible_to_users={is_visible}, status={status}")
                        return False
                else:
                    self.log_test("Policy Default Values", False, "Could not find created policy")
                    return False
            else:
                self.log_test("Policy Default Values", False, f"Failed to get policies: {response.status_code}")
                return False
        else:
            self.log_test("Policy Default Values", False, f"Failed to create policy: {response.status_code} - {response.text}")
            return False

    def test_document_default_values(self):
        """Test that documents get correct default values"""
        print("\n🔍 Testing Document Default Values...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create minimal document upload
        test_file = io.BytesIO(b"Test document content")
        form_data = {
            'title': 'Default Values Test Document',
            'document_type': 'document',
            'category_id': self.test_category_id,
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department'
            # Note: NOT setting is_visible_to_users or status explicitly
        }
        
        files = {'file': ('test.txt', test_file, 'text/plain')}
        
        response = requests.post(f"{self.api_url}/documents", 
                               data=form_data, files=files, headers=headers)
        
        if response.status_code == 200:
            document_data = response.json().get('document', {})
            document_id = document_data.get('id')
            print(f"   Created document ID: {document_id}")
            
            is_visible = document_data.get('is_visible_to_users')
            status = document_data.get('status')
            
            print(f"   Default is_visible_to_users: {is_visible}")
            print(f"   Default status: {status}")
            
            # Check if defaults are correct
            if is_visible is True and status == 'active':
                self.log_test("Document Default Values", True, 
                            f"is_visible_to_users={is_visible}, status={status}")
                return True
            else:
                self.log_test("Document Default Values", False, 
                            f"Expected is_visible_to_users=True and status='active', got is_visible_to_users={is_visible}, status={status}")
                return False
        else:
            self.log_test("Document Default Values", False, f"Failed to create document: {response.status_code} - {response.text}")
            return False

    def test_public_api_filtering(self):
        """Test that public APIs properly filter by visibility and status"""
        print("\n🔍 Testing Public API Filtering...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # First, create a policy and set it to hidden
        test_file = io.BytesIO(b"Hidden policy content")
        form_data = {
            'title': 'Hidden Policy Test',
            'category_id': self.test_category_id,
            'policy_type_id': self.test_policy_type_id,
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department'
        }
        
        files = {'file': ('hidden_test.pdf', test_file, 'application/pdf')}
        
        response = requests.post(f"{self.api_url}/policies", 
                               data=form_data, files=files, headers=headers)
        
        if response.status_code == 200:
            policy_number = response.json().get('policy_number')
            
            # Find the policy ID
            response = requests.get(f"{self.api_url}/policies", headers=headers)
            policy_id = None
            for policy in response.json():
                if policy.get('policy_number') == policy_number:
                    policy_id = policy.get('id')
                    break
            
            if policy_id:
                # Hide the policy from users
                response = requests.patch(f"{self.api_url}/policies/{policy_id}/visibility",
                                        headers=headers,
                                        params={"is_visible": "false"})
                
                if response.status_code == 200:
                    print(f"   Successfully hid policy {policy_number}")
                    
                    # Now check if it appears in public API
                    response = requests.get(f"{self.api_url}/public/policies")
                    if response.status_code == 200:
                        public_policies = response.json()
                        hidden_policy_found = False
                        for policy in public_policies:
                            if policy.get('id') == policy_id:
                                hidden_policy_found = True
                                break
                        
                        if not hidden_policy_found:
                            self.log_test("Public API Filtering", True, 
                                        "Hidden policy correctly excluded from public API")
                            return True
                        else:
                            self.log_test("Public API Filtering", False, 
                                        "Hidden policy incorrectly appears in public API")
                            return False
                    else:
                        self.log_test("Public API Filtering", False, 
                                    f"Failed to get public policies: {response.status_code}")
                        return False
                else:
                    self.log_test("Public API Filtering", False, 
                                f"Failed to hide policy: {response.status_code}")
                    return False
            else:
                self.log_test("Public API Filtering", False, "Could not find created policy")
                return False
        else:
            self.log_test("Public API Filtering", False, f"Failed to create test policy: {response.status_code}")
            return False

    def test_status_filtering(self):
        """Test that deleted documents don't appear in public API"""
        print("\n🔍 Testing Status Filtering...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create a document
        test_file = io.BytesIO(b"Document to be deleted")
        form_data = {
            'title': 'Document to Delete',
            'document_type': 'document',
            'category_id': self.test_category_id,
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department'
        }
        
        files = {'file': ('delete_test.txt', test_file, 'text/plain')}
        
        response = requests.post(f"{self.api_url}/documents", 
                               data=form_data, files=files, headers=headers)
        
        if response.status_code == 200:
            document_id = response.json().get('document', {}).get('id')
            
            if document_id:
                # Delete the document
                response = requests.delete(f"{self.api_url}/documents/{document_id}",
                                         headers=headers)
                
                if response.status_code == 200:
                    print(f"   Successfully deleted document {document_id}")
                    
                    # Check if it appears in public API
                    response = requests.get(f"{self.api_url}/public/documents")
                    if response.status_code == 200:
                        public_documents = response.json()
                        deleted_doc_found = False
                        for doc in public_documents:
                            if doc.get('id') == document_id:
                                deleted_doc_found = True
                                break
                        
                        if not deleted_doc_found:
                            self.log_test("Status Filtering", True, 
                                        "Deleted document correctly excluded from public API")
                            return True
                        else:
                            self.log_test("Status Filtering", False, 
                                        "Deleted document incorrectly appears in public API")
                            return False
                    else:
                        self.log_test("Status Filtering", False, 
                                    f"Failed to get public documents: {response.status_code}")
                        return False
                else:
                    self.log_test("Status Filtering", False, 
                                f"Failed to delete document: {response.status_code}")
                    return False
            else:
                self.log_test("Status Filtering", False, "Could not get document ID")
                return False
        else:
            self.log_test("Status Filtering", False, f"Failed to create test document: {response.status_code}")
            return False

    def run_tests(self):
        """Run all default value tests"""
        print("🔍 DOCUMENT DEFAULTS AND EDGE CASES TEST")
        print("=" * 60)
        
        if not self.setup_auth_and_data():
            print("❌ Setup failed. Cannot proceed.")
            return False
        
        # Run tests
        self.test_policy_default_values()
        self.test_document_default_values()
        self.test_public_api_filtering()
        self.test_status_filtering()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = DocumentDefaultsTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())