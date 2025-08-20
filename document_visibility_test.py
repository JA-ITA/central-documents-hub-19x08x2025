#!/usr/bin/env python3
"""
Document Visibility Investigation Test
=====================================
This test specifically investigates why documents are not visible when uploaded.
It tests the document upload process and visibility settings.
"""

import requests
import sys
import json
import io
from datetime import datetime
from pathlib import Path

class DocumentVisibilityTester:
    def __init__(self, base_url="https://codebase-check-12.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_user = None
        self.test_category_id = None
        self.test_policy_type_id = None
        self.uploaded_policy_id = None
        self.uploaded_document_id = None
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
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            # Don't set Content-Type for file uploads - let requests handle it
            pass
        else:
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
                if params:
                    response = requests.patch(url, headers=headers, params=params)
                else:
                    response = requests.patch(url, json=data, headers=headers)
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
        """Setup admin authentication"""
        print("🔐 Setting up admin authentication...")
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

    def get_test_category_and_type(self):
        """Get or create test category and policy type"""
        print("\n📁 Getting test category and policy type...")
        
        # Get categories
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if success and response:
            categories = response if isinstance(response, list) else []
            if categories:
                self.test_category_id = categories[0]['id']
                print(f"   Using category: {categories[0]['name']} (ID: {self.test_category_id})")
        
        # Get policy types
        success, response = self.run_test(
            "Get Policy Types",
            "GET",
            "policy-types",
            200
        )
        
        if success and response:
            policy_types = response if isinstance(response, list) else []
            if policy_types:
                self.test_policy_type_id = policy_types[0]['id']
                print(f"   Using policy type: {policy_types[0]['name']} (ID: {self.test_policy_type_id})")
        
        return self.test_category_id and self.test_policy_type_id

    def create_test_pdf_file(self):
        """Create a simple test PDF file"""
        # Create a simple text file that we'll treat as a PDF for testing
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        return io.BytesIO(pdf_content)

    def test_policy_upload(self):
        """Test policy upload and check visibility settings"""
        print("\n📄 Testing Policy Upload...")
        
        if not self.test_category_id or not self.test_policy_type_id:
            self.log_test("Policy Upload", False, "Missing category or policy type")
            return False
        
        # Create test PDF file
        test_file = self.create_test_pdf_file()
        
        # Prepare form data
        form_data = {
            'title': 'Test Policy for Visibility Investigation',
            'category_id': self.test_category_id,
            'policy_type_id': self.test_policy_type_id,
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department',
            'change_summary': 'Initial version for visibility testing'
        }
        
        files = {
            'file': ('test_policy.pdf', test_file, 'application/pdf')
        }
        
        success, response = self.run_test(
            "Upload Policy Document",
            "POST",
            "policies",
            200,
            data=form_data,
            files=files
        )
        
        if success:
            print(f"   Policy upload response: {response}")
            # Try to extract policy number or ID from response
            if isinstance(response, dict):
                policy_number = response.get('policy_number')
                if policy_number:
                    print(f"   Created policy number: {policy_number}")
                    # We need to find the policy ID by searching for this policy
                    return self.find_uploaded_policy(policy_number)
        
        return success

    def find_uploaded_policy(self, policy_number):
        """Find the uploaded policy by policy number"""
        print(f"\n🔍 Finding uploaded policy with number: {policy_number}")
        
        success, response = self.run_test(
            "Get All Policies (Admin View)",
            "GET",
            "policies",
            200,
            params={"include_hidden": "true", "include_deleted": "true"}
        )
        
        if success and response:
            policies = response if isinstance(response, list) else []
            for policy in policies:
                if policy.get('policy_number') == policy_number:
                    self.uploaded_policy_id = policy.get('id')
                    print(f"   Found uploaded policy ID: {self.uploaded_policy_id}")
                    print(f"   Policy visibility settings:")
                    print(f"     - is_visible_to_users: {policy.get('is_visible_to_users')}")
                    print(f"     - status: {policy.get('status')}")
                    print(f"     - title: {policy.get('title')}")
                    return True
        
        self.log_test("Find Uploaded Policy", False, f"Could not find policy with number {policy_number}")
        return False

    def test_document_upload(self):
        """Test document upload and check visibility settings"""
        print("\n📄 Testing Document Upload...")
        
        if not self.test_category_id:
            self.log_test("Document Upload", False, "Missing category")
            return False
        
        # Create test text file
        test_file = io.BytesIO(b"This is a test document for visibility investigation.")
        
        # Prepare form data
        form_data = {
            'title': 'Test Document for Visibility Investigation',
            'document_type': 'document',
            'category_id': self.test_category_id,
            'date_issued': datetime.now().isoformat(),
            'owner_department': 'Test Department',
            'description': 'Test document to check visibility settings'
        }
        
        files = {
            'file': ('test_document.txt', test_file, 'text/plain')
        }
        
        success, response = self.run_test(
            "Upload Document",
            "POST",
            "documents",
            200,
            data=form_data,
            files=files
        )
        
        if success and response:
            print(f"   Document upload response: {response}")
            if isinstance(response, dict) and 'document' in response:
                document = response['document']
                self.uploaded_document_id = document.get('id')
                print(f"   Created document ID: {self.uploaded_document_id}")
                print(f"   Document visibility settings:")
                print(f"     - is_visible_to_users: {document.get('is_visible_to_users')}")
                print(f"     - status: {document.get('status')}")
                print(f"     - title: {document.get('title')}")
                return True
        
        return success

    def test_public_policy_visibility(self):
        """Test if uploaded policy appears in public API"""
        print("\n🌐 Testing Public Policy Visibility...")
        
        # Test public policies endpoint (no auth required)
        headers_backup = self.token
        self.token = None  # Remove auth for public endpoint
        
        success, response = self.run_test(
            "Get Public Policies",
            "GET",
            "public/policies",
            200
        )
        
        self.token = headers_backup  # Restore auth
        
        if success and response:
            policies = response if isinstance(response, list) else []
            print(f"   Found {len(policies)} public policies")
            
            # Check if our uploaded policy is visible
            if self.uploaded_policy_id:
                found_policy = None
                for policy in policies:
                    if policy.get('id') == self.uploaded_policy_id:
                        found_policy = policy
                        break
                
                if found_policy:
                    print(f"   ✅ Uploaded policy IS visible in public API")
                    print(f"     - Title: {found_policy.get('title')}")
                    print(f"     - Status: {found_policy.get('status')}")
                    print(f"     - Visible to users: {found_policy.get('is_visible_to_users')}")
                    return True
                else:
                    print(f"   ❌ Uploaded policy NOT visible in public API")
                    print(f"   Policy ID being searched: {self.uploaded_policy_id}")
                    return False
            else:
                print(f"   ⚠️  No uploaded policy ID to check")
                return False
        
        return success

    def test_public_document_visibility(self):
        """Test if uploaded document appears in public API"""
        print("\n🌐 Testing Public Document Visibility...")
        
        # Test public documents endpoint (no auth required)
        headers_backup = self.token
        self.token = None  # Remove auth for public endpoint
        
        success, response = self.run_test(
            "Get Public Documents",
            "GET",
            "public/documents",
            200
        )
        
        self.token = headers_backup  # Restore auth
        
        if success and response:
            documents = response if isinstance(response, list) else []
            print(f"   Found {len(documents)} public documents")
            
            # Check if our uploaded document is visible
            if self.uploaded_document_id:
                found_document = None
                for document in documents:
                    if document.get('id') == self.uploaded_document_id:
                        found_document = document
                        break
                
                if found_document:
                    print(f"   ✅ Uploaded document IS visible in public API")
                    print(f"     - Title: {found_document.get('title')}")
                    print(f"     - Status: {found_document.get('status')}")
                    print(f"     - Visible to users: {found_document.get('is_visible_to_users')}")
                    return True
                else:
                    print(f"   ❌ Uploaded document NOT visible in public API")
                    print(f"   Document ID being searched: {self.uploaded_document_id}")
                    return False
            else:
                print(f"   ⚠️  No uploaded document ID to check")
                return False
        
        return success

    def test_admin_policy_visibility(self):
        """Test if uploaded policy appears in admin API"""
        print("\n👨‍💼 Testing Admin Policy Visibility...")
        
        success, response = self.run_test(
            "Get Admin Policies",
            "GET",
            "policies",
            200
        )
        
        if success and response:
            policies = response if isinstance(response, list) else []
            print(f"   Found {len(policies)} admin policies")
            
            # Check if our uploaded policy is visible
            if self.uploaded_policy_id:
                found_policy = None
                for policy in policies:
                    if policy.get('id') == self.uploaded_policy_id:
                        found_policy = policy
                        break
                
                if found_policy:
                    print(f"   ✅ Uploaded policy IS visible in admin API")
                    print(f"     - Title: {found_policy.get('title')}")
                    print(f"     - Status: {found_policy.get('status')}")
                    print(f"     - Visible to users: {found_policy.get('is_visible_to_users')}")
                    return True
                else:
                    print(f"   ❌ Uploaded policy NOT visible in admin API")
                    return False
        
        return success

    def test_admin_document_visibility(self):
        """Test if uploaded document appears in admin API"""
        print("\n👨‍💼 Testing Admin Document Visibility...")
        
        success, response = self.run_test(
            "Get Admin Documents",
            "GET",
            "documents",
            200
        )
        
        if success and response:
            documents = response if isinstance(response, list) else []
            print(f"   Found {len(documents)} admin documents")
            
            # Check if our uploaded document is visible
            if self.uploaded_document_id:
                found_document = None
                for document in documents:
                    if document.get('id') == self.uploaded_document_id:
                        found_document = document
                        break
                
                if found_document:
                    print(f"   ✅ Uploaded document IS visible in admin API")
                    print(f"     - Title: {found_document.get('title')}")
                    print(f"     - Status: {found_document.get('status')}")
                    print(f"     - Visible to users: {found_document.get('is_visible_to_users')}")
                    return True
                else:
                    print(f"   ❌ Uploaded document NOT visible in admin API")
                    return False
        
        return success

    def investigate_database_state(self):
        """Investigate the current database state"""
        print("\n🔍 Investigating Database State...")
        
        # Get all policies with all flags
        success, response = self.run_test(
            "Get All Policies (All Flags)",
            "GET",
            "policies",
            200,
            params={"include_hidden": "true", "include_deleted": "true"}
        )
        
        if success and response:
            policies = response if isinstance(response, list) else []
            print(f"\n📊 Database State Analysis:")
            print(f"   Total policies in database: {len(policies)}")
            
            visible_count = 0
            hidden_count = 0
            active_count = 0
            deleted_count = 0
            archived_count = 0
            
            for policy in policies:
                if policy.get('is_visible_to_users', True):
                    visible_count += 1
                else:
                    hidden_count += 1
                
                status = policy.get('status', 'unknown')
                if status == 'active':
                    active_count += 1
                elif status == 'deleted':
                    deleted_count += 1
                elif status == 'archived':
                    archived_count += 1
            
            print(f"   Visibility breakdown:")
            print(f"     - Visible to users: {visible_count}")
            print(f"     - Hidden from users: {hidden_count}")
            print(f"   Status breakdown:")
            print(f"     - Active: {active_count}")
            print(f"     - Archived: {archived_count}")
            print(f"     - Deleted: {deleted_count}")
            
            # Show details of recent policies
            print(f"\n   Recent policies (last 3):")
            for policy in policies[-3:]:
                print(f"     - {policy.get('title', 'Unknown')}:")
                print(f"       ID: {policy.get('id')}")
                print(f"       Status: {policy.get('status')}")
                print(f"       Visible: {policy.get('is_visible_to_users')}")
                print(f"       Created: {policy.get('created_at', 'Unknown')}")

    def run_investigation(self):
        """Run the complete document visibility investigation"""
        print("🔍 DOCUMENT VISIBILITY INVESTIGATION")
        print("=" * 60)
        print("This test investigates why documents are not visible when uploaded.")
        print()
        
        # Setup
        if not self.setup_admin_auth():
            print("❌ Cannot authenticate as admin. Stopping investigation.")
            return False
        
        if not self.get_test_category_and_type():
            print("❌ Cannot get test category and policy type. Stopping investigation.")
            return False
        
        # Investigate current database state
        self.investigate_database_state()
        
        # Test policy upload
        print("\n" + "=" * 40)
        print("TESTING POLICY UPLOAD")
        print("=" * 40)
        self.test_policy_upload()
        
        # Test document upload
        print("\n" + "=" * 40)
        print("TESTING DOCUMENT UPLOAD")
        print("=" * 40)
        self.test_document_upload()
        
        # Test visibility in different APIs
        print("\n" + "=" * 40)
        print("TESTING VISIBILITY IN APIS")
        print("=" * 40)
        self.test_public_policy_visibility()
        self.test_public_document_visibility()
        self.test_admin_policy_visibility()
        self.test_admin_document_visibility()
        
        # Final summary
        print("\n" + "=" * 60)
        print("🔍 INVESTIGATION SUMMARY")
        print("=" * 60)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        # Analyze results
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['message']}")
        
        print("\n🔍 KEY FINDINGS:")
        if self.uploaded_policy_id:
            print(f"   - Policy uploaded successfully (ID: {self.uploaded_policy_id})")
        else:
            print("   - Policy upload failed or policy not found")
        
        if self.uploaded_document_id:
            print(f"   - Document uploaded successfully (ID: {self.uploaded_document_id})")
        else:
            print("   - Document upload failed or document not found")
        
        return self.tests_passed >= (self.tests_run * 0.7)  # 70% pass rate

def main():
    tester = DocumentVisibilityTester()
    success = tester.run_investigation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())