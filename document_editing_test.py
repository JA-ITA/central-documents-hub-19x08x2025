import requests
import sys
import json
import io
from datetime import datetime
import tempfile
import os

class DocumentEditingTester:
    def __init__(self, base_url="https://secure-doc-viewer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.manager_token = None
        self.user_token = None
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

    def create_test_pdf_file(self):
        """Create a simple test PDF file"""
        # Create a minimal PDF content
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
72 720 Td
(Test Document) Tj
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

    def create_test_docx_file(self):
        """Create a simple test DOCX file"""
        # Create a minimal DOCX content (simplified ZIP structure)
        docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00Test Document Content"
        return io.BytesIO(docx_content)

    def login_user(self, username, password, role_name):
        """Login and get token for a user"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": username, "password": password},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                user = data.get('user', {})
                print(f"✅ {role_name} login successful - Role: {user.get('role')}")
                return token
            else:
                print(f"❌ {role_name} login failed - Status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ {role_name} login error: {str(e)}")
            return None

    def setup_test_data(self):
        """Setup test data including policy, category, and policy type"""
        print("\n🔧 Setting up test data...")
        
        # Login as admin
        self.admin_token = self.login_user("admin", "admin123", "Admin")
        if not self.admin_token:
            return False

        headers = {
            'Authorization': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }

        # Get existing categories
        try:
            response = requests.get(f"{self.api_url}/categories", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                if categories:
                    self.test_category_id = categories[0]['id']
                    print(f"   Using existing category: {categories[0]['name']} (ID: {self.test_category_id})")
        except Exception as e:
            print(f"   Error getting categories: {str(e)}")

        # Get existing policy types
        try:
            response = requests.get(f"{self.api_url}/policy-types", headers=headers)
            if response.status_code == 200:
                policy_types = response.json()
                if policy_types:
                    self.test_policy_type_id = policy_types[0]['id']
                    print(f"   Using existing policy type: {policy_types[0]['name']} (ID: {self.test_policy_type_id})")
        except Exception as e:
            print(f"   Error getting policy types: {str(e)}")

        # Create a test policy for document editing
        if self.test_category_id and self.test_policy_type_id:
            try:
                # Create initial PDF file
                pdf_file = self.create_test_pdf_file()
                
                files = {
                    'file': ('test_policy.pdf', pdf_file, 'application/pdf')
                }
                data = {
                    'title': 'Test Policy for Document Editing',
                    'category_id': self.test_category_id,
                    'policy_type_id': self.test_policy_type_id,
                    'date_issued': '2025-01-01T00:00:00Z',
                    'owner_department': 'Test Department',
                    'change_summary': 'Initial test policy creation'
                }
                
                headers_upload = {'Authorization': f'Bearer {self.admin_token}'}
                response = requests.post(
                    f"{self.api_url}/policies",
                    data=data,
                    files=files,
                    headers=headers_upload
                )
                
                if response.status_code == 200:
                    # Get the created policy ID
                    policies_response = requests.get(f"{self.api_url}/policies", headers=headers)
                    if policies_response.status_code == 200:
                        policies = policies_response.json()
                        for policy in policies:
                            if policy['title'] == 'Test Policy for Document Editing':
                                self.test_policy_id = policy['id']
                                print(f"   Created test policy: {policy['title']} (ID: {self.test_policy_id})")
                                break
                else:
                    print(f"   Failed to create test policy: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"   Error creating test policy: {str(e)}")

        return self.test_policy_id is not None

    def test_authentication_authorization(self):
        """Test authentication and authorization for document editing endpoint"""
        print("\n=== AUTHENTICATION & AUTHORIZATION TESTS ===")
        
        if not self.test_policy_id:
            self.log_test("Auth Setup", False, "No test policy available")
            return False

        # Test 1: Admin access
        try:
            pdf_file = self.create_test_pdf_file()
            files = {'file': ('updated_policy.pdf', pdf_file, 'application/pdf')}
            data = {'change_summary': 'Admin test update'}
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            success = response.status_code == 200
            self.log_test(
                "Admin Document Edit Access", 
                success, 
                f"Status: {response.status_code}" + (f" - {response.json()}" if success else f" - {response.text}")
            )
        except Exception as e:
            self.log_test("Admin Document Edit Access", False, f"Exception: {str(e)}")

        # Test 2: Policy Manager access (create policy manager user first)
        try:
            # Create policy manager user
            manager_data = {
                "username": f"testmanager_{datetime.now().strftime('%H%M%S')}",
                "email": f"manager_{datetime.now().strftime('%H%M%S')}@test.com",
                "full_name": "Test Policy Manager",
                "password": "manager123"
            }
            
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=manager_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get('id')
                
                # Approve and set role as admin
                admin_headers = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}
                
                # Approve user
                requests.patch(f"{self.api_url}/users/{user_id}/approve", headers=admin_headers)
                
                # Set role to policy_manager
                requests.patch(
                    f"{self.api_url}/users/{user_id}/role",
                    headers=admin_headers,
                    params={"role": "policy_manager"}
                )
                
                # Login as policy manager
                self.manager_token = self.login_user(manager_data["username"], "manager123", "Policy Manager")
                
                if self.manager_token:
                    pdf_file = self.create_test_pdf_file()
                    files = {'file': ('manager_updated_policy.pdf', pdf_file, 'application/pdf')}
                    data = {'change_summary': 'Policy manager test update'}
                    headers = {'Authorization': f'Bearer {self.manager_token}'}
                    
                    response = requests.patch(
                        f"{self.api_url}/policies/{self.test_policy_id}/document",
                        data=data,
                        files=files,
                        headers=headers
                    )
                    
                    success = response.status_code == 200
                    self.log_test(
                        "Policy Manager Document Edit Access", 
                        success, 
                        f"Status: {response.status_code}" + (f" - {response.json()}" if success else f" - {response.text}")
                    )
                else:
                    self.log_test("Policy Manager Document Edit Access", False, "Failed to login as policy manager")
            else:
                self.log_test("Policy Manager Document Edit Access", False, "Failed to create policy manager user")
                
        except Exception as e:
            self.log_test("Policy Manager Document Edit Access", False, f"Exception: {str(e)}")

        # Test 3: Regular user access (should be denied)
        try:
            # Create regular user
            user_data = {
                "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
                "email": f"user_{datetime.now().strftime('%H%M%S')}@test.com",
                "full_name": "Test Regular User",
                "password": "user123"
            }
            
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                user_response_data = response.json()
                user_id = user_response_data.get('id')
                
                # Approve user as admin
                admin_headers = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}
                requests.patch(f"{self.api_url}/users/{user_id}/approve", headers=admin_headers)
                
                # Login as regular user
                self.user_token = self.login_user(user_data["username"], "user123", "Regular User")
                
                if self.user_token:
                    pdf_file = self.create_test_pdf_file()
                    files = {'file': ('user_updated_policy.pdf', pdf_file, 'application/pdf')}
                    data = {'change_summary': 'Regular user test update'}
                    headers = {'Authorization': f'Bearer {self.user_token}'}
                    
                    response = requests.patch(
                        f"{self.api_url}/policies/{self.test_policy_id}/document",
                        data=data,
                        files=files,
                        headers=headers
                    )
                    
                    # Should be denied (403)
                    success = response.status_code == 403
                    self.log_test(
                        "Regular User Document Edit Denied", 
                        success, 
                        f"Status: {response.status_code} (Expected 403)" + (f" - {response.text}" if not success else " - Access properly denied")
                    )
                else:
                    self.log_test("Regular User Document Edit Denied", False, "Failed to login as regular user")
            else:
                self.log_test("Regular User Document Edit Denied", False, "Failed to create regular user")
                
        except Exception as e:
            self.log_test("Regular User Document Edit Denied", False, f"Exception: {str(e)}")

        # Test 4: Invalid/expired token
        try:
            pdf_file = self.create_test_pdf_file()
            files = {'file': ('invalid_token_policy.pdf', pdf_file, 'application/pdf')}
            data = {'change_summary': 'Invalid token test'}
            headers = {'Authorization': 'Bearer invalid_token_12345'}
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            # Should be unauthorized (401)
            success = response.status_code == 401
            self.log_test(
                "Invalid Token Denied", 
                success, 
                f"Status: {response.status_code} (Expected 401)" + (f" - {response.text}" if not success else " - Invalid token properly denied")
            )
        except Exception as e:
            self.log_test("Invalid Token Denied", False, f"Exception: {str(e)}")

        return True

    def test_document_upload_replacement(self):
        """Test document upload and replacement functionality"""
        print("\n=== DOCUMENT UPLOAD & REPLACEMENT TESTS ===")
        
        if not self.test_policy_id or not self.admin_token:
            self.log_test("Document Upload Setup", False, "Missing test policy or admin token")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}

        # Test 1: Successful PDF replacement
        try:
            pdf_file = self.create_test_pdf_file()
            files = {'file': ('updated_policy.pdf', pdf_file, 'application/pdf')}
            data = {'change_summary': 'Updated PDF document'}
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            success = response.status_code == 200
            response_data = response.json() if success else response.text
            self.log_test(
                "PDF Document Replacement", 
                success, 
                f"Status: {response.status_code}" + (f" - New version: {response_data.get('new_version', 'N/A')}" if success else f" - {response_data}")
            )
        except Exception as e:
            self.log_test("PDF Document Replacement", False, f"Exception: {str(e)}")

        # Test 2: Successful DOCX replacement
        try:
            docx_file = self.create_test_docx_file()
            files = {'file': ('updated_policy.docx', docx_file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {'change_summary': 'Updated DOCX document'}
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            success = response.status_code == 200
            response_data = response.json() if success else response.text
            self.log_test(
                "DOCX Document Replacement", 
                success, 
                f"Status: {response.status_code}" + (f" - New version: {response_data.get('new_version', 'N/A')}" if success else f" - {response_data}")
            )
        except Exception as e:
            self.log_test("DOCX Document Replacement", False, f"Exception: {str(e)}")

        # Test 3: Invalid file type rejection
        try:
            # Create a fake TXT file
            txt_file = io.BytesIO(b"This is a text file, not allowed")
            files = {'file': ('invalid_file.txt', txt_file, 'text/plain')}
            data = {'change_summary': 'Invalid file type test'}
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            # Should be rejected (400)
            success = response.status_code == 400
            self.log_test(
                "Invalid File Type Rejection", 
                success, 
                f"Status: {response.status_code} (Expected 400)" + (f" - {response.text}" if not success else " - Invalid file type properly rejected")
            )
        except Exception as e:
            self.log_test("Invalid File Type Rejection", False, f"Exception: {str(e)}")

        # Test 4: File size handling (create a larger file)
        try:
            # Create a larger PDF file (still small for testing)
            large_pdf_content = b"%PDF-1.4\n" + b"Large content " * 1000 + b"\n%%EOF"
            large_pdf_file = io.BytesIO(large_pdf_content)
            files = {'file': ('large_policy.pdf', large_pdf_file, 'application/pdf')}
            data = {'change_summary': 'Large file test'}
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            # Should succeed (assuming reasonable size limits)
            success = response.status_code == 200
            response_data = response.json() if success else response.text
            self.log_test(
                "Large File Upload", 
                success, 
                f"Status: {response.status_code}" + (f" - File uploaded successfully" if success else f" - {response_data}")
            )
        except Exception as e:
            self.log_test("Large File Upload", False, f"Exception: {str(e)}")

        return True

    def test_version_management(self):
        """Test version management functionality"""
        print("\n=== VERSION MANAGEMENT TESTS ===")
        
        if not self.test_policy_id or not self.admin_token:
            self.log_test("Version Management Setup", False, "Missing test policy or admin token")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}

        # Get initial policy state
        try:
            response = requests.get(f"{self.api_url}/policies/{self.test_policy_id}", headers=headers)
            if response.status_code == 200:
                initial_policy = response.json()
                initial_version = initial_policy.get('version', 1)
                initial_history_count = len(initial_policy.get('version_history', []))
                
                print(f"   Initial policy version: {initial_version}")
                print(f"   Initial version history entries: {initial_history_count}")
                
                # Test version increment
                pdf_file = self.create_test_pdf_file()
                files = {'file': ('version_test.pdf', pdf_file, 'application/pdf')}
                data = {'change_summary': 'Version increment test'}
                upload_headers = {'Authorization': f'Bearer {self.admin_token}'}
                
                response = requests.patch(
                    f"{self.api_url}/policies/{self.test_policy_id}/document",
                    data=data,
                    files=files,
                    headers=upload_headers
                )
                
                if response.status_code == 200:
                    update_response = response.json()
                    new_version = update_response.get('new_version')
                    
                    # Verify version incremented
                    version_incremented = new_version == initial_version + 1
                    self.log_test(
                        "Version Number Increment", 
                        version_incremented, 
                        f"Version changed from {initial_version} to {new_version}"
                    )
                    
                    # Get updated policy to check version history
                    response = requests.get(f"{self.api_url}/policies/{self.test_policy_id}", headers=headers)
                    if response.status_code == 200:
                        updated_policy = response.json()
                        new_history_count = len(updated_policy.get('version_history', []))
                        
                        # Verify version history updated
                        history_updated = new_history_count == initial_history_count + 1
                        self.log_test(
                            "Version History Updated", 
                            history_updated, 
                            f"History entries changed from {initial_history_count} to {new_history_count}"
                        )
                        
                        # Check latest version history entry
                        if updated_policy.get('version_history'):
                            latest_entry = updated_policy['version_history'][-1]
                            
                            # Check version number in history
                            correct_version = latest_entry.get('version_number') == new_version
                            self.log_test(
                                "Version History Entry Version", 
                                correct_version, 
                                f"Latest entry version: {latest_entry.get('version_number')}"
                            )
                            
                            # Check uploaded_by field
                            has_uploaded_by = 'uploaded_by' in latest_entry and latest_entry['uploaded_by']
                            self.log_test(
                                "Version History Uploaded By", 
                                has_uploaded_by, 
                                f"Uploaded by: {latest_entry.get('uploaded_by', 'Missing')}"
                            )
                            
                            # Check change_summary
                            has_change_summary = 'change_summary' in latest_entry and latest_entry['change_summary']
                            self.log_test(
                                "Version History Change Summary", 
                                has_change_summary, 
                                f"Change summary: {latest_entry.get('change_summary', 'Missing')}"
                            )
                            
                            # Check file_url
                            has_file_url = 'file_url' in latest_entry and latest_entry['file_url']
                            self.log_test(
                                "Version History File URL", 
                                has_file_url, 
                                f"File URL: {latest_entry.get('file_url', 'Missing')}"
                            )
                    else:
                        self.log_test("Version History Check", False, "Failed to get updated policy")
                else:
                    self.log_test("Version Management", False, f"Document update failed: {response.status_code}")
            else:
                self.log_test("Version Management Setup", False, "Failed to get initial policy state")
        except Exception as e:
            self.log_test("Version Management", False, f"Exception: {str(e)}")

        return True

    def test_policy_data_updates(self):
        """Test policy data updates after document replacement"""
        print("\n=== POLICY DATA UPDATES TESTS ===")
        
        if not self.test_policy_id or not self.admin_token:
            self.log_test("Policy Data Updates Setup", False, "Missing test policy or admin token")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}

        try:
            # Get initial policy state
            response = requests.get(f"{self.api_url}/policies/{self.test_policy_id}", headers=headers)
            if response.status_code == 200:
                initial_policy = response.json()
                initial_file_url = initial_policy.get('file_url')
                initial_file_name = initial_policy.get('file_name')
                initial_version = initial_policy.get('version')
                initial_modified_by = initial_policy.get('modified_by')
                initial_modified_at = initial_policy.get('modified_at')
                initial_policy_id = initial_policy.get('id')
                
                print(f"   Initial file URL: {initial_file_url}")
                print(f"   Initial file name: {initial_file_name}")
                print(f"   Initial version: {initial_version}")
                
                # Update document
                pdf_file = self.create_test_pdf_file()
                files = {'file': ('policy_data_test.pdf', pdf_file, 'application/pdf')}
                data = {'change_summary': 'Policy data update test'}
                upload_headers = {'Authorization': f'Bearer {self.admin_token}'}
                
                response = requests.patch(
                    f"{self.api_url}/policies/{self.test_policy_id}/document",
                    data=data,
                    files=files,
                    headers=upload_headers
                )
                
                if response.status_code == 200:
                    # Get updated policy
                    response = requests.get(f"{self.api_url}/policies/{self.test_policy_id}", headers=headers)
                    if response.status_code == 200:
                        updated_policy = response.json()
                        
                        # Test file_url updated
                        new_file_url = updated_policy.get('file_url')
                        file_url_updated = new_file_url != initial_file_url
                        self.log_test(
                            "File URL Updated", 
                            file_url_updated, 
                            f"URL changed from {initial_file_url} to {new_file_url}"
                        )
                        
                        # Test file_name updated
                        new_file_name = updated_policy.get('file_name')
                        file_name_updated = new_file_name == 'policy_data_test.pdf'
                        self.log_test(
                            "File Name Updated", 
                            file_name_updated, 
                            f"Name changed to: {new_file_name}"
                        )
                        
                        # Test version updated
                        new_version = updated_policy.get('version')
                        version_updated = new_version == initial_version + 1
                        self.log_test(
                            "Version Updated", 
                            version_updated, 
                            f"Version changed from {initial_version} to {new_version}"
                        )
                        
                        # Test modified_by set
                        new_modified_by = updated_policy.get('modified_by')
                        modified_by_set = new_modified_by == 'admin'
                        self.log_test(
                            "Modified By Set", 
                            modified_by_set, 
                            f"Modified by: {new_modified_by}"
                        )
                        
                        # Test modified_at set
                        new_modified_at = updated_policy.get('modified_at')
                        modified_at_set = new_modified_at is not None and new_modified_at != initial_modified_at
                        self.log_test(
                            "Modified At Set", 
                            modified_at_set, 
                            f"Modified at: {new_modified_at}"
                        )
                        
                        # Test policy ID unchanged
                        policy_id_unchanged = updated_policy.get('id') == initial_policy_id
                        self.log_test(
                            "Policy ID Unchanged", 
                            policy_id_unchanged, 
                            f"Policy ID: {updated_policy.get('id')}"
                        )
                        
                        # Test other core data unchanged (title, category_id, etc.)
                        title_unchanged = updated_policy.get('title') == initial_policy.get('title')
                        category_unchanged = updated_policy.get('category_id') == initial_policy.get('category_id')
                        policy_type_unchanged = updated_policy.get('policy_type_id') == initial_policy.get('policy_type_id')
                        
                        core_data_unchanged = title_unchanged and category_unchanged and policy_type_unchanged
                        self.log_test(
                            "Core Data Unchanged", 
                            core_data_unchanged, 
                            f"Title, category, and policy type preserved"
                        )
                    else:
                        self.log_test("Policy Data Updates", False, "Failed to get updated policy")
                else:
                    self.log_test("Policy Data Updates", False, f"Document update failed: {response.status_code}")
            else:
                self.log_test("Policy Data Updates Setup", False, "Failed to get initial policy")
        except Exception as e:
            self.log_test("Policy Data Updates", False, f"Exception: {str(e)}")

        return True

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n=== ERROR HANDLING TESTS ===")
        
        if not self.admin_token:
            self.log_test("Error Handling Setup", False, "Missing admin token")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}

        # Test 1: Non-existent policy ID
        try:
            pdf_file = self.create_test_pdf_file()
            files = {'file': ('nonexistent_test.pdf', pdf_file, 'application/pdf')}
            data = {'change_summary': 'Non-existent policy test'}
            
            fake_policy_id = "nonexistent-policy-id-12345"
            response = requests.patch(
                f"{self.api_url}/policies/{fake_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            # Should return 404
            success = response.status_code == 404
            self.log_test(
                "Non-existent Policy ID (404)", 
                success, 
                f"Status: {response.status_code} (Expected 404)" + (f" - {response.text}" if not success else " - Properly returned 404")
            )
        except Exception as e:
            self.log_test("Non-existent Policy ID (404)", False, f"Exception: {str(e)}")

        # Test 2: Missing file upload
        try:
            data = {'change_summary': 'Missing file test'}
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                headers=headers
            )
            
            # Should return validation error (422)
            success = response.status_code == 422
            self.log_test(
                "Missing File Upload (422)", 
                success, 
                f"Status: {response.status_code} (Expected 422)" + (f" - {response.text}" if not success else " - Properly returned validation error")
            )
        except Exception as e:
            self.log_test("Missing File Upload (422)", False, f"Exception: {str(e)}")

        # Test 3: Empty change summary (should use default)
        try:
            pdf_file = self.create_test_pdf_file()
            files = {'file': ('empty_summary_test.pdf', pdf_file, 'application/pdf')}
            data = {}  # No change_summary provided
            
            response = requests.patch(
                f"{self.api_url}/policies/{self.test_policy_id}/document",
                data=data,
                files=files,
                headers=headers
            )
            
            # Should succeed and use default summary
            success = response.status_code == 200
            self.log_test(
                "Empty Change Summary (Default Used)", 
                success, 
                f"Status: {response.status_code}" + (f" - Default summary used" if success else f" - {response.text}")
            )
            
            # Verify default summary was used
            if success:
                headers_json = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}
                policy_response = requests.get(f"{self.api_url}/policies/{self.test_policy_id}", headers=headers_json)
                if policy_response.status_code == 200:
                    policy = policy_response.json()
                    version_history = policy.get('version_history', [])
                    if version_history:
                        latest_entry = version_history[-1]
                        change_summary = latest_entry.get('change_summary', '')
                        default_used = change_summary == 'Document updated'
                        self.log_test(
                            "Default Change Summary Applied", 
                            default_used, 
                            f"Summary: '{change_summary}'"
                        )
        except Exception as e:
            self.log_test("Empty Change Summary (Default Used)", False, f"Exception: {str(e)}")

        return True

    def test_existing_functionality_regression(self):
        """Test that existing functionality still works"""
        print("\n=== REGRESSION TESTS (EXISTING FUNCTIONALITY) ===")
        
        if not self.admin_token:
            self.log_test("Regression Test Setup", False, "Missing admin token")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}

        # Test 1: Get policies still works
        try:
            response = requests.get(f"{self.api_url}/policies", headers=headers)
            success = response.status_code == 200
            self.log_test(
                "Get Policies Still Works", 
                success, 
                f"Status: {response.status_code}" + (f" - Found {len(response.json())} policies" if success else f" - {response.text}")
            )
        except Exception as e:
            self.log_test("Get Policies Still Works", False, f"Exception: {str(e)}")

        # Test 2: Get single policy still works
        if self.test_policy_id:
            try:
                response = requests.get(f"{self.api_url}/policies/{self.test_policy_id}", headers=headers)
                success = response.status_code == 200
                self.log_test(
                    "Get Single Policy Still Works", 
                    success, 
                    f"Status: {response.status_code}" + (f" - Policy retrieved" if success else f" - {response.text}")
                )
            except Exception as e:
                self.log_test("Get Single Policy Still Works", False, f"Exception: {str(e)}")

        # Test 3: Authentication system still works
        try:
            response = requests.get(f"{self.api_url}/auth/me", headers=headers)
            success = response.status_code == 200
            self.log_test(
                "Authentication System Still Works", 
                success, 
                f"Status: {response.status_code}" + (f" - User info retrieved" if success else f" - {response.text}")
            )
        except Exception as e:
            self.log_test("Authentication System Still Works", False, f"Exception: {str(e)}")

        # Test 4: File download still works
        if self.test_policy_id:
            try:
                response = requests.get(f"{self.api_url}/policies/{self.test_policy_id}/download", headers=headers)
                success = response.status_code == 200
                self.log_test(
                    "File Download Still Works", 
                    success, 
                    f"Status: {response.status_code}" + (f" - File downloaded" if success else f" - {response.text}")
                )
            except Exception as e:
                self.log_test("File Download Still Works", False, f"Exception: {str(e)}")

        # Test 5: Policy visibility toggle still works
        if self.test_policy_id:
            try:
                response = requests.patch(
                    f"{self.api_url}/policies/{self.test_policy_id}/visibility",
                    headers=headers,
                    params={"is_visible": "false"}
                )
                success = response.status_code == 200
                self.log_test(
                    "Policy Visibility Toggle Still Works", 
                    success, 
                    f"Status: {response.status_code}" + (f" - Visibility toggled" if success else f" - {response.text}")
                )
                
                # Toggle back
                if success:
                    requests.patch(
                        f"{self.api_url}/policies/{self.test_policy_id}/visibility",
                        headers=headers,
                        params={"is_visible": "true"}
                    )
            except Exception as e:
                self.log_test("Policy Visibility Toggle Still Works", False, f"Exception: {str(e)}")

        return True

    def run_all_tests(self):
        """Run all document editing tests"""
        print("🚀 Starting Document Editing Functionality Tests")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Failed to setup test data. Cannot proceed.")
            return False
        
        # Run all test suites
        self.test_authentication_authorization()
        self.test_document_upload_replacement()
        self.test_version_management()
        self.test_policy_data_updates()
        self.test_error_handling()
        self.test_existing_functionality_regression()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Document Editing Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All document editing tests passed!")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed")
            
            # Show failed tests
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
            
            return False

def main():
    tester = DocumentEditingTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())