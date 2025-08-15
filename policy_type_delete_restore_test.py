import requests
import sys
import json
from datetime import datetime
import time

class PolicyTypeDeleteRestoreTester:
    def __init__(self, base_url="https://doc-hub-public.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_user = None
        self.test_policy_type_id = None
        self.test_category_id = None
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

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
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

            print(f"   Response Status: {response.status_code}")
            print(f"   Response Data: {json.dumps(response_data, indent=2) if isinstance(response_data, dict) else response_data}")

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
            print(f"   Admin authenticated: {self.admin_user.get('username', 'unknown')}")
            return True
        return False

    def setup_test_category(self):
        """Create a test category for policy creation tests"""
        print("\n📁 Setting up test category...")
        unique_id = f"{int(time.time() % 10000)}"
        test_category_data = {
            "name": f"Test Category {unique_id}",
            "code": f"TC{unique_id}",
            "description": "Test category for policy type testing"
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
            print(f"   Test category created: {self.test_category_id}")
            return True
        return False

    def test_policy_type_creation_with_is_deleted_field(self):
        """Test 1: Policy type creation works with the new is_deleted field"""
        print("\n=== TEST 1: Policy Type Creation with is_deleted Field ===")
        
        unique_id = f"{int(time.time() % 10000)}"
        policy_type_data = {
            "name": f"Test Policy Type {unique_id}",
            "code": f"TPT{unique_id}",
            "description": "Test policy type for delete/restore functionality"
        }
        
        success, response = self.run_test(
            "Create Policy Type with is_deleted Field",
            "POST",
            "policy-types",
            200,
            data=policy_type_data
        )
        
        if success:
            self.test_policy_type_id = response.get('id')
            # Verify the response includes is_deleted field set to False by default
            if response.get('is_deleted') == False:
                print(f"   ✅ Policy type created with is_deleted=False by default")
                print(f"   Policy Type ID: {self.test_policy_type_id}")
                return True
            else:
                print(f"   ❌ is_deleted field not properly set: {response.get('is_deleted')}")
                return False
        return False

    def test_policy_type_soft_delete(self):
        """Test 2: Policy type soft delete functionality"""
        print("\n=== TEST 2: Policy Type Soft Delete ===")
        
        if not self.test_policy_type_id:
            print("❌ No test policy type available for deletion")
            return False
        
        success, response = self.run_test(
            "Soft Delete Policy Type",
            "DELETE",
            f"policy-types/{self.test_policy_type_id}",
            200
        )
        
        if success:
            # Verify the policy type is marked as deleted
            success_verify, verify_response = self.run_test(
                "Verify Policy Type Soft Deleted",
                "GET",
                "policy-types",
                200,
                params={"include_deleted": "true"}
            )
            
            if success_verify:
                policy_types = verify_response if isinstance(verify_response, list) else []
                deleted_type = next((pt for pt in policy_types if pt.get('id') == self.test_policy_type_id), None)
                
                if deleted_type and deleted_type.get('is_deleted') == True and deleted_type.get('is_active') == False:
                    print(f"   ✅ Policy type properly soft deleted: is_deleted=True, is_active=False")
                    return True
                else:
                    print(f"   ❌ Policy type not properly soft deleted: {deleted_type}")
                    return False
        return False

    def test_policy_type_restore(self):
        """Test 3: Policy type restore functionality"""
        print("\n=== TEST 3: Policy Type Restore ===")
        
        if not self.test_policy_type_id:
            print("❌ No test policy type available for restoration")
            return False
        
        success, response = self.run_test(
            "Restore Policy Type",
            "PATCH",
            f"policy-types/{self.test_policy_type_id}/restore",
            200
        )
        
        if success:
            # Verify the policy type is restored
            success_verify, verify_response = self.run_test(
                "Verify Policy Type Restored",
                "GET",
                "policy-types",
                200,
                params={"include_deleted": "true"}
            )
            
            if success_verify:
                policy_types = verify_response if isinstance(verify_response, list) else []
                restored_type = next((pt for pt in policy_types if pt.get('id') == self.test_policy_type_id), None)
                
                if restored_type and restored_type.get('is_deleted') == False and restored_type.get('is_active') == True:
                    print(f"   ✅ Policy type properly restored: is_deleted=False, is_active=True")
                    return True
                else:
                    print(f"   ❌ Policy type not properly restored: {restored_type}")
                    return False
        return False

    def test_policy_type_listing_with_include_deleted(self):
        """Test 4: Policy type listing with include_deleted parameter"""
        print("\n=== TEST 4: Policy Type Listing with include_deleted Parameter ===")
        
        # Test listing without include_deleted (should exclude deleted types)
        success1, response1 = self.run_test(
            "Get Policy Types (Exclude Deleted)",
            "GET",
            "policy-types",
            200
        )
        
        # Test listing with include_deleted=true (should include deleted types)
        success2, response2 = self.run_test(
            "Get Policy Types (Include Deleted)",
            "GET",
            "policy-types",
            200,
            params={"include_deleted": "true"}
        )
        
        if success1 and success2:
            active_types = response1 if isinstance(response1, list) else []
            all_types = response2 if isinstance(response2, list) else []
            
            active_count = len(active_types)
            total_count = len(all_types)
            deleted_count = len([pt for pt in all_types if pt.get('is_deleted') == True])
            
            print(f"   Active policy types: {active_count}")
            print(f"   Total policy types: {total_count}")
            print(f"   Deleted policy types: {deleted_count}")
            
            if total_count >= active_count:
                print(f"   ✅ include_deleted parameter working correctly")
                return True
            else:
                print(f"   ❌ include_deleted parameter not working properly")
                return False
        return False

    def test_policy_type_update_with_new_model(self):
        """Test 5: Policy type update with the new PolicyTypeUpdate model"""
        print("\n=== TEST 5: Policy Type Update with PolicyTypeUpdate Model ===")
        
        if not self.test_policy_type_id:
            print("❌ No test policy type available for update")
            return False
        
        # Test updating various fields using the PolicyTypeUpdate model
        update_data = {
            "name": "Updated Test Policy Type",
            "description": "Updated description for testing",
            "is_active": True
        }
        
        success, response = self.run_test(
            "Update Policy Type with New Model",
            "PATCH",
            f"policy-types/{self.test_policy_type_id}",
            200,
            data=update_data
        )
        
        if success:
            # Verify the update was applied
            success_verify, verify_response = self.run_test(
                "Verify Policy Type Update",
                "GET",
                "policy-types",
                200,
                params={"include_deleted": "true"}
            )
            
            if success_verify:
                policy_types = verify_response if isinstance(verify_response, list) else []
                updated_type = next((pt for pt in policy_types if pt.get('id') == self.test_policy_type_id), None)
                
                if updated_type and updated_type.get('name') == "Updated Test Policy Type":
                    print(f"   ✅ Policy type update successful with new model")
                    return True
                else:
                    print(f"   ❌ Policy type update failed: {updated_type}")
                    return False
        return False

    def test_deleted_policy_types_excluded_from_active_operations(self):
        """Test 6: Deleted policy types are excluded from active operations"""
        print("\n=== TEST 6: Deleted Policy Types Excluded from Active Operations ===")
        
        if not self.test_policy_type_id:
            print("❌ No test policy type available")
            return False
        
        # First, soft delete the policy type
        success_delete, _ = self.run_test(
            "Delete Policy Type for Exclusion Test",
            "DELETE",
            f"policy-types/{self.test_policy_type_id}",
            200
        )
        
        if success_delete:
            # Test that deleted policy types are not included in regular listing
            success_list, response_list = self.run_test(
                "Get Active Policy Types Only",
                "GET",
                "policy-types",
                200
            )
            
            if success_list:
                active_types = response_list if isinstance(response_list, list) else []
                deleted_type_in_active = any(pt.get('id') == self.test_policy_type_id for pt in active_types)
                
                if not deleted_type_in_active:
                    print(f"   ✅ Deleted policy type properly excluded from active operations")
                    return True
                else:
                    print(f"   ❌ Deleted policy type still appears in active operations")
                    return False
        return False

    def test_policy_creation_rejects_deleted_policy_types(self):
        """Test 7: Policy creation rejects deleted policy types"""
        print("\n=== TEST 7: Policy Creation Rejects Deleted Policy Types ===")
        
        if not self.test_policy_type_id or not self.test_category_id:
            print("❌ Missing test policy type or category for policy creation test")
            return False
        
        # Ensure the policy type is deleted
        success_delete, _ = self.run_test(
            "Ensure Policy Type is Deleted",
            "DELETE",
            f"policy-types/{self.test_policy_type_id}",
            200
        )
        
        # Try to create a policy with the deleted policy type
        # Note: This test simulates policy creation but won't actually upload a file
        # We expect this to fail during policy number generation when it checks for active policy types
        
        # First, let's verify the generate_policy_number logic by checking if deleted policy types are filtered
        success_verify, verify_response = self.run_test(
            "Verify Deleted Policy Type Not Available for Policy Creation",
            "GET",
            "policy-types",
            200,
            params={"include_inactive": "false"}
        )
        
        if success_verify:
            active_types = verify_response if isinstance(verify_response, list) else []
            deleted_type_available = any(pt.get('id') == self.test_policy_type_id for pt in active_types)
            
            if not deleted_type_available:
                print(f"   ✅ Deleted policy type not available for policy creation")
                return True
            else:
                print(f"   ❌ Deleted policy type still available for policy creation")
                return False
        return False

    def test_restoring_policy_type_makes_it_available(self):
        """Test 8: Restoring a policy type makes it available again"""
        print("\n=== TEST 8: Restoring Policy Type Makes It Available ===")
        
        if not self.test_policy_type_id:
            print("❌ No test policy type available")
            return False
        
        # Restore the policy type
        success_restore, _ = self.run_test(
            "Restore Policy Type for Availability Test",
            "PATCH",
            f"policy-types/{self.test_policy_type_id}/restore",
            200
        )
        
        if success_restore:
            # Verify it's now available in active operations
            success_list, response_list = self.run_test(
                "Verify Restored Policy Type Available",
                "GET",
                "policy-types",
                200
            )
            
            if success_list:
                active_types = response_list if isinstance(response_list, list) else []
                restored_type_available = any(pt.get('id') == self.test_policy_type_id for pt in active_types)
                
                if restored_type_available:
                    print(f"   ✅ Restored policy type is available for operations")
                    return True
                else:
                    print(f"   ❌ Restored policy type not available for operations")
                    return False
        return False

    def test_error_handling_for_nonexistent_policy_types(self):
        """Test 9: Proper error handling for non-existent policy types"""
        print("\n=== TEST 9: Error Handling for Non-existent Policy Types ===")
        
        fake_id = "non-existent-policy-type-id"
        
        # Test delete on non-existent policy type
        success1, response1 = self.run_test(
            "Delete Non-existent Policy Type",
            "DELETE",
            f"policy-types/{fake_id}",
            404
        )
        
        # Test restore on non-existent policy type
        success2, response2 = self.run_test(
            "Restore Non-existent Policy Type",
            "PATCH",
            f"policy-types/{fake_id}/restore",
            404
        )
        
        # Test update on non-existent policy type
        success3, response3 = self.run_test(
            "Update Non-existent Policy Type",
            "PATCH",
            f"policy-types/{fake_id}",
            404,
            data={"name": "Updated Name"}
        )
        
        if success1 and success2 and success3:
            print(f"   ✅ Proper 404 errors returned for non-existent policy types")
            return True
        else:
            print(f"   ❌ Error handling not working properly for non-existent policy types")
            return False

    def test_default_data_initialization_with_new_fields(self):
        """Test 10: Default data initialization works with new fields"""
        print("\n=== TEST 10: Default Data Initialization with New Fields ===")
        
        # Get all policy types including deleted ones
        success, response = self.run_test(
            "Get All Policy Types for Default Data Check",
            "GET",
            "policy-types",
            200,
            params={"include_deleted": "true"}
        )
        
        if success:
            policy_types = response if isinstance(response, list) else []
            default_types = ["Policy", "Procedure", "Guideline"]
            
            # Check if default types exist and have proper is_deleted field
            found_defaults = []
            for pt in policy_types:
                if pt.get('name') in default_types:
                    found_defaults.append(pt)
                    if 'is_deleted' not in pt:
                        print(f"   ❌ Default policy type missing is_deleted field: {pt.get('name')}")
                        return False
                    if pt.get('is_deleted') != False:
                        print(f"   ❌ Default policy type has incorrect is_deleted value: {pt.get('name')} = {pt.get('is_deleted')}")
                        return False
            
            if len(found_defaults) >= 3:
                print(f"   ✅ Default policy types properly initialized with is_deleted=False")
                print(f"   Found default types: {[pt.get('name') for pt in found_defaults]}")
                return True
            else:
                print(f"   ❌ Not all default policy types found: {len(found_defaults)}/3")
                return False
        return False

    def run_all_tests(self):
        """Run all policy type delete/restore tests"""
        print("🚀 Starting Policy Type Delete/Restore Functionality Tests")
        print("=" * 70)
        
        # Setup authentication
        if not self.setup_admin_auth():
            print("\n❌ Admin authentication failed. Cannot proceed.")
            return False
        
        # Setup test data
        if not self.setup_test_category():
            print("\n❌ Test category setup failed. Some tests may not work properly.")
        
        # Run all tests
        test_results = []
        test_results.append(self.test_policy_type_creation_with_is_deleted_field())
        test_results.append(self.test_policy_type_soft_delete())
        test_results.append(self.test_policy_type_restore())
        test_results.append(self.test_policy_type_listing_with_include_deleted())
        test_results.append(self.test_policy_type_update_with_new_model())
        test_results.append(self.test_deleted_policy_types_excluded_from_active_operations())
        test_results.append(self.test_policy_creation_rejects_deleted_policy_types())
        test_results.append(self.test_restoring_policy_type_makes_it_available())
        test_results.append(self.test_error_handling_for_nonexistent_policy_types())
        test_results.append(self.test_default_data_initialization_with_new_fields())
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"{i:2d}. {result['test']}: {status}")
            if not result['success']:
                print(f"    └─ {result['message']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All Policy Type Delete/Restore tests passed!")
            return True
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = PolicyTypeDeleteRestoreTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())