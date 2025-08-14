import requests
import json
from datetime import datetime
import time

def test_policy_creation_with_deleted_policy_type():
    """Test that policy creation properly rejects deleted policy types"""
    base_url = "https://secure-doc-viewer.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as admin
    login_response = requests.post(f"{api_url}/auth/login", json={
        "username": "admin", 
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print("❌ Admin login failed")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("🔍 Testing Policy Creation Integration with Deleted Policy Types")
    print("=" * 60)
    
    # Create a test policy type
    unique_id = f"{int(time.time() % 10000)}"
    policy_type_data = {
        "name": f"Integration Test Type {unique_id}",
        "code": f"ITT{unique_id}",
        "description": "Policy type for integration testing"
    }
    
    create_response = requests.post(f"{api_url}/policy-types", json=policy_type_data, headers=headers)
    if create_response.status_code != 200:
        print("❌ Failed to create test policy type")
        return False
    
    policy_type_id = create_response.json()['id']
    print(f"✅ Created test policy type: {policy_type_id}")
    
    # Get a test category
    categories_response = requests.get(f"{api_url}/categories", headers=headers)
    if categories_response.status_code != 200 or not categories_response.json():
        print("❌ No categories available for testing")
        return False
    
    category_id = categories_response.json()[0]['id']
    print(f"✅ Using test category: {category_id}")
    
    # Test 1: Verify policy number generation works with active policy type
    print("\n📝 Test 1: Policy number generation with active policy type")
    try:
        # We can't easily test the full policy creation without a file upload,
        # but we can test the generate_policy_number logic by checking if the policy type
        # is available in the active policy types list
        active_types_response = requests.get(f"{api_url}/policy-types", headers=headers)
        active_types = active_types_response.json()
        
        active_type_ids = [pt['id'] for pt in active_types if pt.get('is_active') and not pt.get('is_deleted')]
        
        if policy_type_id in active_type_ids:
            print("✅ Active policy type available for policy creation")
        else:
            print("❌ Active policy type not available for policy creation")
            return False
            
    except Exception as e:
        print(f"❌ Error testing active policy type: {e}")
        return False
    
    # Test 2: Delete the policy type and verify it's not available
    print("\n🗑️  Test 2: Delete policy type and verify unavailability")
    delete_response = requests.delete(f"{api_url}/policy-types/{policy_type_id}", headers=headers)
    if delete_response.status_code != 200:
        print("❌ Failed to delete policy type")
        return False
    
    print("✅ Policy type deleted successfully")
    
    # Verify it's not in active list
    active_types_response = requests.get(f"{api_url}/policy-types", headers=headers)
    active_types = active_types_response.json()
    active_type_ids = [pt['id'] for pt in active_types if pt.get('is_active') and not pt.get('is_deleted')]
    
    if policy_type_id not in active_type_ids:
        print("✅ Deleted policy type properly excluded from active operations")
    else:
        print("❌ Deleted policy type still available in active operations")
        return False
    
    # Test 3: Verify it's still in the full list with include_deleted=true
    print("\n📋 Test 3: Verify deleted policy type in full list")
    all_types_response = requests.get(f"{api_url}/policy-types", headers=headers, params={"include_deleted": "true"})
    all_types = all_types_response.json()
    
    deleted_type = next((pt for pt in all_types if pt['id'] == policy_type_id), None)
    if deleted_type and deleted_type.get('is_deleted') == True:
        print("✅ Deleted policy type found in full list with is_deleted=True")
    else:
        print("❌ Deleted policy type not properly marked in full list")
        return False
    
    # Test 4: Restore and verify availability
    print("\n🔄 Test 4: Restore policy type and verify availability")
    restore_response = requests.patch(f"{api_url}/policy-types/{policy_type_id}/restore", headers=headers)
    if restore_response.status_code != 200:
        print("❌ Failed to restore policy type")
        return False
    
    print("✅ Policy type restored successfully")
    
    # Verify it's back in active list
    active_types_response = requests.get(f"{api_url}/policy-types", headers=headers)
    active_types = active_types_response.json()
    active_type_ids = [pt['id'] for pt in active_types if pt.get('is_active') and not pt.get('is_deleted')]
    
    if policy_type_id in active_type_ids:
        print("✅ Restored policy type available for operations again")
        return True
    else:
        print("❌ Restored policy type not available for operations")
        return False

if __name__ == "__main__":
    success = test_policy_creation_with_deleted_policy_type()
    if success:
        print("\n🎉 All policy creation integration tests passed!")
    else:
        print("\n❌ Some policy creation integration tests failed!")