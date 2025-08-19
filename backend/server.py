from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import shutil
from enum import Enum

ROOT_DIR = Path(__file__).parent
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = "policy-register-secret-key-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    POLICY_MANAGER = "policy_manager" 
    USER = "user"

class PolicyStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    HIDDEN = "hidden"  # Hidden from regular users
    DELETED = "deleted"  # Soft deleted

# New Enums for Documents
class DocumentType(str, Enum):
    POLICY = "policy"
    MEMO = "memo"
    DOCUMENT = "document"
    PROCEDURE = "procedure"
    GUIDELINE = "guideline"
    NOTICE = "notice"

# User Group Models
class UserGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    description: Optional[str] = ""
    department: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserGroupCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""
    department: Optional[str] = None

class UserGroupUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None

class PolicyType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    description: Optional[str] = ""
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PolicyTypeCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""

class PolicyTypeUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: UserRole = UserRole.USER
    user_group_ids: List[str] = []  # User can belong to multiple groups
    is_approved: bool = False
    is_active: bool = True
    is_suspended: bool = False
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    password_hash: str

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    user_group_ids: Optional[List[str]] = None
    is_approved: Optional[bool] = None
    is_active: Optional[bool] = None
    is_suspended: Optional[bool] = None
    is_deleted: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    description: Optional[str] = ""
    parent_id: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CategoryCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""
    parent_id: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None

class DocumentVersion(BaseModel):
    version_number: int
    upload_date: datetime
    uploaded_by: str
    change_summary: Optional[str] = ""
    file_url: str
    file_name: str

# Enhanced Document model (more general than Policy)
class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_number: str
    title: str
    document_type: DocumentType = DocumentType.DOCUMENT
    category_id: str
    policy_type_id: Optional[str] = None  # Only for policies
    date_issued: datetime
    version: int = 1
    status: PolicyStatus = PolicyStatus.ACTIVE
    owner_department: str
    file_url: str
    file_name: str
    is_visible_to_users: bool = True  # Public visibility (no login required)
    visible_to_groups: List[str] = []  # Group-specific visibility (requires login)
    version_history: List[DocumentVersion] = []
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    description: Optional[str] = ""
    tags: List[str] = []

class DocumentCreate(BaseModel):
    title: str
    document_type: DocumentType = DocumentType.DOCUMENT
    category_id: str
    policy_type_id: Optional[str] = None
    date_issued: datetime
    owner_department: str
    document_number: Optional[str] = None
    description: Optional[str] = ""
    tags: Optional[List[str]] = []

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    document_type: Optional[DocumentType] = None
    category_id: Optional[str] = None
    policy_type_id: Optional[str] = None
    date_issued: Optional[datetime] = None
    owner_department: Optional[str] = None
    status: Optional[PolicyStatus] = None
    is_visible_to_users: Optional[bool] = None
    visible_to_groups: Optional[List[str]] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class PolicyVersion(BaseModel):
    version_number: int
    upload_date: datetime
    uploaded_by: str
    change_summary: Optional[str] = ""
    file_url: str
    file_name: str

class Policy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    policy_number: str
    title: str
    category_id: str
    policy_type_id: str  # Changed from enum to reference
    date_issued: datetime
    version: int = 1
    status: PolicyStatus = PolicyStatus.ACTIVE
    owner_department: str
    file_url: str
    file_name: str
    is_visible_to_users: bool = True
    version_history: List[PolicyVersion] = []
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None

class PolicyCreate(BaseModel):
    title: str
    category_id: str
    policy_type_id: str  # Changed from enum to reference
    date_issued: datetime
    owner_department: str
    policy_number: Optional[str] = None

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[str] = None
    policy_type_id: Optional[str] = None
    date_issued: Optional[datetime] = None
    owner_department: Optional[str] = None
    status: Optional[PolicyStatus] = None
    is_visible_to_users: Optional[bool] = None

# Utility Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"username": username, "is_deleted": False})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.get("is_suspended", False):
        raise HTTPException(status_code=401, detail="Account suspended")
    
    user.pop('_id', None)  # Remove MongoDB ObjectId
    return User(**user)

async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def require_admin_or_manager(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.POLICY_MANAGER]:
        raise HTTPException(status_code=403, detail="Admin or Policy Manager access required")
    return current_user

async def generate_policy_number(category_id: str, policy_type_id: str, year: int) -> str:
    # Get category
    category = await db.categories.find_one({"id": category_id, "is_deleted": False})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get policy type
    policy_type = await db.policy_types.find_one({"id": policy_type_id, "is_active": True, "is_deleted": False})
    if not policy_type:
        raise HTTPException(status_code=404, detail="Policy type not found")
    
    category_code = category["code"]
    type_code = policy_type["code"]
    
    # Get next sequential number for this category and year
    existing_policies = await db.policies.find({
        "category_id": category_id,
        "date_issued": {
            "$gte": datetime(year, 1, 1),
            "$lt": datetime(year + 1, 1, 1)
        },
        "status": {"$ne": "deleted"}
    }).to_list(None)
    
    next_seq = len(existing_policies) + 1
    
    return f"{category_code}-{type_code}-{next_seq:03d}-{year}-v1"

# Initialize default data
async def init_default_data():
    # Check if admin user exists
    admin_exists = await db.users.find_one({"role": UserRole.ADMIN, "is_deleted": False})
    if not admin_exists:
        admin_user = User(
            username="admin",
            email="admin@policyhub.com",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_approved=True,
            is_active=True,
            password_hash=hash_password("admin123")
        )
        await db.users.insert_one(admin_user.dict())
        print("Default admin user created: username=admin, password=admin123")
    
    # Check if default category exists
    ops_category = await db.categories.find_one({"code": "OPS", "is_deleted": False})
    if not ops_category:
        default_category = Category(
            name="Operations",
            code="OPS",
            description="Operational policies and procedures"
        )
        await db.categories.insert_one(default_category.dict())
        print("Default Operations category created")
    
    # Check if default policy types exist
    default_types = [
        {"name": "Policy", "code": "P", "description": "Standard organizational policies"},
        {"name": "Procedure", "code": "PR", "description": "Step-by-step procedures"},
        {"name": "Guideline", "code": "G", "description": "Guidelines and recommendations"}
    ]
    
    for type_data in default_types:
        existing_type = await db.policy_types.find_one({"code": type_data["code"], "is_deleted": False})
        if not existing_type:
            policy_type = PolicyType(**type_data)
            await db.policy_types.insert_one(policy_type.dict())
            print(f"Default policy type created: {type_data['name']}")

# Authentication Routes
@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"username": user_data.username, "is_deleted": False})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = await db.users.find_one({"email": user_data.email, "is_deleted": False})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hashed_password,
        is_approved=False  # Requires admin approval
    )
    
    await db.users.insert_one(user.dict())
    user_dict = user.dict()
    user_dict.pop('password_hash')
    return User(**user_dict, password_hash="")

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username, "is_deleted": False})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user["is_approved"] or not user["is_active"] or user.get("is_suspended", False):
        raise HTTPException(status_code=401, detail="Account not approved, inactive, or suspended")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    user_data = user.copy()
    user_data.pop('password_hash')
    user_data.pop('_id', None)  # Remove MongoDB ObjectId
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    user_dict = current_user.dict()
    user_dict.pop('password_hash', None)
    return User(**user_dict, password_hash="")

# Policy Type Routes
@api_router.post("/policy-types", response_model=PolicyType)
async def create_policy_type(policy_type_data: PolicyTypeCreate, current_user: User = Depends(require_admin_or_manager)):
    # Check if code already exists
    existing_type = await db.policy_types.find_one({"code": policy_type_data.code.upper(), "is_deleted": False})
    if existing_type:
        raise HTTPException(status_code=400, detail="Policy type code already exists")
    
    # Create policy type with uppercase code
    policy_type_dict = policy_type_data.dict()
    policy_type_dict["code"] = policy_type_data.code.upper()
    policy_type = PolicyType(**policy_type_dict)
    await db.policy_types.insert_one(policy_type.dict())
    return policy_type

@api_router.get("/policy-types", response_model=List[PolicyType])
async def get_policy_types(include_inactive: bool = False, include_deleted: bool = False, current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role in [UserRole.ADMIN, UserRole.POLICY_MANAGER] and include_deleted:
        # Admin and Policy Manager can see deleted policy types
        pass
    else:
        query["is_deleted"] = False
        if not include_inactive:
            query["is_active"] = True
    
    policy_types = await db.policy_types.find(query).to_list(None)
    result = []
    for pt in policy_types:
        pt.pop('_id', None)
        result.append(PolicyType(**pt))
    return result

@api_router.patch("/policy-types/{type_id}")
async def update_policy_type(type_id: str, update_data: PolicyTypeUpdate, current_user: User = Depends(require_admin_or_manager)):
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        result = await db.policy_types.update_one(
            {"id": type_id},
            {"$set": update_dict}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy type not found")
    return {"message": "Policy type updated successfully"}

@api_router.delete("/policy-types/{type_id}")
async def delete_policy_type(type_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.policy_types.update_one(
        {"id": type_id},
        {"$set": {"is_deleted": True, "is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Policy type not found")
    return {"message": "Policy type deleted successfully"}

@api_router.patch("/policy-types/{type_id}/restore")
async def restore_policy_type(type_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.policy_types.update_one(
        {"id": type_id},
        {"$set": {"is_deleted": False, "is_active": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Policy type not found")
    return {"message": "Policy type restored successfully"}

# Category Routes
@api_router.post("/categories", response_model=Category)
async def create_category(category_data: CategoryCreate, current_user: User = Depends(require_admin_or_manager)):
    # Check if code already exists
    existing_category = await db.categories.find_one({"code": category_data.code.upper(), "is_deleted": False})
    if existing_category:
        raise HTTPException(status_code=400, detail="Category code already exists")
    
    category_dict = category_data.dict()
    category_dict["code"] = category_data.code.upper()
    category = Category(**category_dict)
    await db.categories.insert_one(category.dict())
    return category

@api_router.get("/categories", response_model=List[Category])
async def get_categories(include_deleted: bool = False, current_user: User = Depends(get_current_user)):
    if current_user.role in [UserRole.ADMIN, UserRole.POLICY_MANAGER] and include_deleted:
        query = {}
    else:
        query = {"is_deleted": False, "is_active": True}
    
    categories = await db.categories.find(query).to_list(None)
    result = []
    for cat in categories:
        cat.pop('_id', None)  # Remove MongoDB ObjectId
        result.append(Category(**cat))
    return result

@api_router.patch("/categories/{category_id}")
async def update_category(category_id: str, update_data: CategoryUpdate, current_user: User = Depends(require_admin_or_manager)):
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        result = await db.categories.update_one(
            {"id": category_id},
            {"$set": update_dict}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category updated successfully"}

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": {"is_deleted": True, "is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

@api_router.patch("/categories/{category_id}/restore")
async def restore_category(category_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": {"is_deleted": False, "is_active": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category restored successfully"}

# Public Routes (No Authentication Required)
@api_router.get("/public/policies", response_model=List[Policy])
async def get_public_policies(
    status: Optional[PolicyStatus] = None,
    category_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Public endpoint to get all policies visible to users"""
    query = {
        "status": {"$in": ["active", "archived"]},
        "is_visible_to_users": True
    }
    
    if status and status in ["active", "archived"]:
        query["status"] = status
    if category_id:
        query["category_id"] = category_id
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"policy_number": {"$regex": search, "$options": "i"}},
            {"owner_department": {"$regex": search, "$options": "i"}}
        ]
    
    policies = await db.policies.find(query).to_list(None)
    result = []
    for policy in policies:
        policy.pop('_id', None)  # Remove MongoDB ObjectId
        result.append(Policy(**policy))
    return result

@api_router.get("/public/policies/{policy_id}", response_model=Policy)
async def get_public_policy(policy_id: str):
    """Public endpoint to get a specific policy if it's visible to users"""
    policy = await db.policies.find_one({
        "id": policy_id,
        "status": {"$in": ["active", "archived"]},
        "is_visible_to_users": True
    })
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy.pop('_id', None)  # Remove MongoDB ObjectId
    return Policy(**policy)

@api_router.get("/public/policies/{policy_id}/download")
async def download_public_policy(policy_id: str):
    """Public endpoint to download a policy document if it's visible to users"""
    policy = await db.policies.find_one({
        "id": policy_id,
        "status": {"$in": ["active", "archived"]},
        "is_visible_to_users": True
    })
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    file_path = UPLOAD_DIR / policy["file_url"].split("/")[-1]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=policy["file_name"],
        media_type='application/octet-stream'
    )

@api_router.get("/public/categories", response_model=List[Category])
async def get_public_categories():
    """Public endpoint to get all active categories"""
    categories = await db.categories.find({
        "is_deleted": False, 
        "is_active": True
    }).to_list(None)
    result = []
    for cat in categories:
        cat.pop('_id', None)  # Remove MongoDB ObjectId
        result.append(Category(**cat))
    return result

@api_router.get("/public/policy-types", response_model=List[PolicyType])
async def get_public_policy_types():
    """Public endpoint to get all active policy types"""
    policy_types = await db.policy_types.find({
        "is_deleted": False,
        "is_active": True
    }).to_list(None)
    result = []
    for pt in policy_types:
        pt.pop('_id', None)
        result.append(PolicyType(**pt))
    return result

# Policy Routes
@api_router.post("/policies")
async def create_policy(
    title: str = Form(...),
    category_id: str = Form(...),
    policy_type_id: str = Form(...),
    date_issued: str = Form(...),
    owner_department: str = Form(...),
    policy_number: Optional[str] = Form(None),
    change_summary: Optional[str] = Form("Initial version"),
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_manager)
):
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    # Parse date
    try:
        issued_date = datetime.fromisoformat(date_issued.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Generate policy number if not provided
    if not policy_number:
        policy_number = await generate_policy_number(category_id, policy_type_id, issued_date.year)
    
    # Save file
    file_extension = file.filename.split('.')[-1]
    saved_filename = f"{policy_number.replace('-', '_')}_v1.{file_extension}"
    file_path = UPLOAD_DIR / saved_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_url = f"/uploads/{saved_filename}"
    
    # Create policy
    policy = Policy(
        policy_number=policy_number,
        title=title,
        category_id=category_id,
        policy_type_id=policy_type_id,
        date_issued=issued_date,
        owner_department=owner_department,
        file_url=file_url,
        file_name=file.filename,
        created_by=current_user.username,
        version_history=[PolicyVersion(
            version_number=1,
            upload_date=datetime.utcnow(),
            uploaded_by=current_user.username,
            change_summary=change_summary or "Initial version",
            file_url=file_url,
            file_name=file.filename
        )]
    )
    
    await db.policies.insert_one(policy.dict())
    return {"message": "Policy created successfully", "policy_number": policy_number}

@api_router.get("/policies", response_model=List[Policy])
async def get_policies(
    status: Optional[PolicyStatus] = None,
    category_id: Optional[str] = None,
    include_hidden: bool = False,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Admin and Policy Manager can see all policies
    if current_user.role in [UserRole.ADMIN, UserRole.POLICY_MANAGER]:
        if not include_deleted:
            query["status"] = {"$ne": "deleted"}
        if not include_hidden and not include_deleted:
            query["$or"] = [
                {"is_visible_to_users": True},
                {"status": {"$in": ["active", "archived"]}}
            ]
    else:
        # Regular users only see visible, non-deleted policies
        query.update({
            "status": {"$in": ["active", "archived"]},
            "is_visible_to_users": True
        })
    
    if status:
        query["status"] = status
    if category_id:
        query["category_id"] = category_id
    
    policies = await db.policies.find(query).to_list(None)
    result = []
    for policy in policies:
        policy.pop('_id', None)  # Remove MongoDB ObjectId
        result.append(Policy(**policy))
    return result

@api_router.get("/policies/{policy_id}", response_model=Policy)
async def get_policy(policy_id: str, current_user: User = Depends(get_current_user)):
    policy = await db.policies.find_one({"id": policy_id})
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Check if user can view this policy
    if current_user.role not in [UserRole.ADMIN, UserRole.POLICY_MANAGER]:
        if policy["status"] == "deleted" or not policy.get("is_visible_to_users", True):
            raise HTTPException(status_code=404, detail="Policy not found")
    
    policy.pop('_id', None)  # Remove MongoDB ObjectId
    return Policy(**policy)

@api_router.patch("/policies/{policy_id}")
async def update_policy(policy_id: str, update_data: PolicyUpdate, current_user: User = Depends(require_admin_or_manager)):
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        update_dict["modified_by"] = current_user.username
        update_dict["modified_at"] = datetime.utcnow()
        
        result = await db.policies.update_one(
            {"id": policy_id},
            {"$set": update_dict}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": "Policy updated successfully"}

@api_router.patch("/policies/{policy_id}/visibility")
async def toggle_policy_visibility(policy_id: str, is_visible: bool, current_user: User = Depends(require_admin_or_manager)):
    result = await db.policies.update_one(
        {"id": policy_id},
        {"$set": {"is_visible_to_users": is_visible, "modified_by": current_user.username, "modified_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": f"Policy {'shown' if is_visible else 'hidden'} successfully"}

@api_router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.policies.update_one(
        {"id": policy_id},
        {"$set": {"status": "deleted", "modified_by": current_user.username, "modified_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": "Policy deleted successfully"}

@api_router.patch("/policies/{policy_id}/restore")
async def restore_policy(policy_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.policies.update_one(
        {"id": policy_id},
        {"$set": {"status": "active", "modified_by": current_user.username, "modified_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": "Policy restored successfully"}

@api_router.patch("/policies/{policy_id}/document")
async def update_policy_document(
    policy_id: str,
    file: UploadFile = File(...),
    change_summary: Optional[str] = Form("Document updated"),
    current_user: User = Depends(require_admin_or_manager)
):
    """Update/replace the document for an existing policy"""
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    # Get existing policy
    existing_policy = await db.policies.find_one({"id": policy_id})
    if not existing_policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Generate new file name with incremented version
    new_version = existing_policy["version"] + 1
    file_extension = file.filename.split('.')[-1]
    policy_number = existing_policy["policy_number"]
    saved_filename = f"{policy_number.replace('-', '_')}_v{new_version}.{file_extension}"
    file_path = UPLOAD_DIR / saved_filename
    
    # Save new file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    new_file_url = f"/uploads/{saved_filename}"
    
    # Create new version history entry
    new_version_entry = PolicyVersion(
        version_number=new_version,
        upload_date=datetime.utcnow(),
        uploaded_by=current_user.username,
        change_summary=change_summary or "Document updated",
        file_url=new_file_url,
        file_name=file.filename
    )
    
    # Update policy with new document and version
    update_data = {
        "version": new_version,
        "file_url": new_file_url,
        "file_name": file.filename,
        "modified_by": current_user.username,
        "modified_at": datetime.utcnow(),
        "$push": {"version_history": new_version_entry.dict()}
    }
    
    result = await db.policies.update_one(
        {"id": policy_id},
        {"$set": {k: v for k, v in update_data.items() if k != "$push"},
         "$push": update_data["$push"]}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Failed to update policy")
    
    return {
        "message": "Policy document updated successfully", 
        "new_version": new_version,
        "file_url": new_file_url
    }

@api_router.get("/policies/{policy_id}/download")
async def download_policy(policy_id: str, current_user: User = Depends(get_current_user)):
    policy = await db.policies.find_one({"id": policy_id})
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Check if user can download this policy
    if current_user.role not in [UserRole.ADMIN, UserRole.POLICY_MANAGER]:
        if policy["status"] == "deleted" or not policy.get("is_visible_to_users", True):
            raise HTTPException(status_code=404, detail="Policy not found")
    
    file_path = UPLOAD_DIR / policy["file_url"].split("/")[-1]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=policy["file_name"],
        media_type='application/octet-stream'
    )

# User Management Routes
@api_router.get("/users", response_model=List[User])
async def get_users(include_deleted: bool = False, current_user: User = Depends(require_admin)):
    query = {} if include_deleted else {"is_deleted": False}
    users = await db.users.find(query).to_list(None)
    result = []
    for user in users:
        user_dict = user.copy()
        user_dict.pop('password_hash', None)
        user_dict.pop('_id', None)  # Remove MongoDB ObjectId
        result.append(User(**user_dict, password_hash=""))
    return result

@api_router.patch("/users/{user_id}")
async def update_user(user_id: str, update_data: UserUpdate, current_user: User = Depends(require_admin)):
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_dict}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}

@api_router.patch("/users/{user_id}/approve")
async def approve_user(user_id: str, current_user: User = Depends(require_admin)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_approved": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User approved successfully"}

@api_router.patch("/users/{user_id}/suspend")
async def suspend_user(user_id: str, current_user: User = Depends(require_admin)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_suspended": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User suspended successfully"}

@api_router.patch("/users/{user_id}/restore")
async def restore_user(user_id: str, current_user: User = Depends(require_admin)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_suspended": False, "is_deleted": False, "is_active": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User restored successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(require_admin)):
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_deleted": True, "is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@api_router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role: UserRole, current_user: User = Depends(require_admin)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User role updated successfully"}

# User Group Routes
@api_router.post("/user-groups", response_model=UserGroup)
async def create_user_group(group_data: UserGroupCreate, current_user: User = Depends(require_admin)):
    # Check if code already exists
    existing_group = await db.user_groups.find_one({"code": group_data.code.upper(), "is_deleted": False})
    if existing_group:
        raise HTTPException(status_code=400, detail="User group code already exists")
    
    user_group = UserGroup(
        name=group_data.name,
        code=group_data.code.upper(),
        description=group_data.description or "",
        department=group_data.department
    )
    
    await db.user_groups.insert_one(user_group.dict())
    return user_group

@api_router.get("/user-groups")
async def get_user_groups(include_deleted: bool = False, current_user: User = Depends(require_admin)):
    query = {}
    if not include_deleted:
        query["is_deleted"] = False
    
    groups = []
    async for group in db.user_groups.find(query):
        group.pop('_id', None)
        groups.append(UserGroup(**group))
    
    return groups

@api_router.get("/user-groups/{group_id}", response_model=UserGroup)
async def get_user_group(group_id: str, current_user: User = Depends(require_admin)):
    group = await db.user_groups.find_one({"id": group_id, "is_deleted": False})
    if not group:
        raise HTTPException(status_code=404, detail="User group not found")
    
    group.pop('_id', None)
    return UserGroup(**group)

@api_router.put("/user-groups/{group_id}", response_model=UserGroup)
async def update_user_group(group_id: str, group_data: UserGroupUpdate, current_user: User = Depends(require_admin)):
    update_data = {}
    if group_data.name is not None:
        update_data["name"] = group_data.name
    if group_data.code is not None:
        # Check if new code already exists (excluding current group)
        existing_group = await db.user_groups.find_one({
            "code": group_data.code.upper(), 
            "is_deleted": False,
            "id": {"$ne": group_id}
        })
        if existing_group:
            raise HTTPException(status_code=400, detail="User group code already exists")
        update_data["code"] = group_data.code.upper()
    if group_data.description is not None:
        update_data["description"] = group_data.description
    if group_data.department is not None:
        update_data["department"] = group_data.department
    if group_data.is_active is not None:
        update_data["is_active"] = group_data.is_active
    if group_data.is_deleted is not None:
        update_data["is_deleted"] = group_data.is_deleted
    
    if update_data:
        result = await db.user_groups.update_one({"id": group_id}, {"$set": update_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User group not found")
    
    # Return updated group
    updated_group = await db.user_groups.find_one({"id": group_id})
    if not updated_group:
        raise HTTPException(status_code=404, detail="User group not found")
    
    updated_group.pop('_id', None)
    return UserGroup(**updated_group)

@api_router.delete("/user-groups/{group_id}")
async def delete_user_group(group_id: str, current_user: User = Depends(require_admin)):
    result = await db.user_groups.update_one(
        {"id": group_id},
        {"$set": {"is_deleted": True, "is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User group not found")
    return {"message": "User group deleted successfully"}

@api_router.patch("/user-groups/{group_id}/restore")
async def restore_user_group(group_id: str, current_user: User = Depends(require_admin)):
    result = await db.user_groups.update_one(
        {"id": group_id},
        {"$set": {"is_deleted": False, "is_active": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User group not found")
    return {"message": "User group restored successfully"}

# Document Routes (Enhanced version of policies)
@api_router.post("/documents")
async def upload_document(
    title: str = Form(...),
    document_type: DocumentType = Form(DocumentType.DOCUMENT),
    category_id: str = Form(...),
    policy_type_id: str = Form(None),
    date_issued: str = Form(...),
    owner_department: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),  # Comma-separated tags
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_manager)
):
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDF, DOCX, DOC, and TXT files are allowed."
        )
    
    # Parse date
    try:
        issued_date = datetime.fromisoformat(date_issued.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
    
    # Verify category exists
    category = await db.categories.find_one({"id": category_id, "is_deleted": False})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Verify policy type if provided
    if policy_type_id:
        policy_type = await db.policy_types.find_one({"id": policy_type_id, "is_active": True, "is_deleted": False})
        if not policy_type:
            raise HTTPException(status_code=404, detail="Policy type not found")
    
    # Generate document number
    year = issued_date.year
    doc_number = await generate_document_number(category_id, policy_type_id, document_type, year)
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document
    document = Document(
        title=title,
        document_type=document_type,
        category_id=category_id,
        policy_type_id=policy_type_id,
        date_issued=issued_date,
        owner_department=owner_department,
        document_number=doc_number,
        description=description,
        tags=tag_list,
        file_url=f"/uploads/{file.filename}",
        file_name=file.filename,
        created_by=current_user.id,
        version_history=[
            DocumentVersion(
                version_number=1,
                upload_date=datetime.utcnow(),
                uploaded_by=current_user.id,
                change_summary="Initial version",
                file_url=f"/uploads/{file.filename}",
                file_name=file.filename
            )
        ]
    )
    
    await db.documents.insert_one(document.dict())
    return {"message": "Document uploaded successfully", "document": document}

async def generate_document_number(category_id: str, policy_type_id: str, document_type: DocumentType, year: int) -> str:
    # Get category
    category = await db.categories.find_one({"id": category_id, "is_deleted": False})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_code = category["code"]
    
    # Get type code
    if policy_type_id:
        policy_type = await db.policy_types.find_one({"id": policy_type_id, "is_active": True, "is_deleted": False})
        type_code = policy_type["code"] if policy_type else document_type.value.upper()[:2]
    else:
        type_code = document_type.value.upper()[:2]
    
    # Get next sequential number for this category and year
    existing_docs = await db.documents.find({
        "category_id": category_id,
        "document_type": document_type,
        "date_issued": {
            "$gte": datetime(year, 1, 1),
            "$lt": datetime(year + 1, 1, 1)
        },
        "status": {"$ne": "deleted"}
    }).to_list(None)
    
    next_seq = len(existing_docs) + 1
    
    return f"{category_code}-{type_code}-{next_seq:03d}-{year}-v1"

@api_router.get("/documents")
async def get_documents(
    search: str = "",
    category_id: str = "",
    document_type: DocumentType = None,
    status: PolicyStatus = None,
    show_hidden: bool = False,
    show_deleted: bool = False,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Admin and policy managers can see all documents
    if current_user.role in [UserRole.ADMIN, UserRole.POLICY_MANAGER]:
        if not show_deleted:
            query["status"] = {"$ne": "deleted"}
        if not show_hidden and current_user.role != UserRole.ADMIN:
            query["$or"] = [
                {"is_visible_to_users": True},
                {"visible_to_groups": {"$in": current_user.user_group_ids}}
            ]
    else:
        # Regular users can only see documents visible to them
        query["status"] = {"$in": ["active", "archived"]}
        query["$or"] = [
            {"is_visible_to_users": True},
            {"visible_to_groups": {"$in": current_user.user_group_ids}}
        ]
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    if category_id:
        query["category_id"] = category_id
    
    if document_type:
        query["document_type"] = document_type
    
    if status:
        query["status"] = status
    
    documents = []
    async for doc in db.documents.find(query):
        doc.pop('_id', None)
        documents.append(Document(**doc))
    
    return documents

@api_router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: str, current_user: User = Depends(get_current_user)):
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.POLICY_MANAGER]:
        if (document.get("status") not in ["active", "archived"] or
            (not document.get("is_visible_to_users", False) and 
             not any(group in current_user.user_group_ids for group in document.get("visible_to_groups", [])))):
            raise HTTPException(status_code=404, detail="Document not found")
    
    document.pop('_id', None)
    return Document(**document)

@api_router.put("/documents/{document_id}", response_model=Document)
async def update_document(
    document_id: str, 
    document_data: DocumentUpdate, 
    current_user: User = Depends(require_admin_or_manager)
):
    # Find existing document
    existing_doc = await db.documents.find_one({"id": document_id})
    if not existing_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Build update data
    update_data = {"modified_by": current_user.id, "modified_at": datetime.utcnow()}
    
    if document_data.title is not None:
        update_data["title"] = document_data.title
    if document_data.document_type is not None:
        update_data["document_type"] = document_data.document_type
    if document_data.category_id is not None:
        # Verify category exists
        category = await db.categories.find_one({"id": document_data.category_id, "is_deleted": False})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        update_data["category_id"] = document_data.category_id
    if document_data.policy_type_id is not None:
        if document_data.policy_type_id:
            policy_type = await db.policy_types.find_one({"id": document_data.policy_type_id, "is_active": True, "is_deleted": False})
            if not policy_type:
                raise HTTPException(status_code=404, detail="Policy type not found")
        update_data["policy_type_id"] = document_data.policy_type_id
    if document_data.date_issued is not None:
        update_data["date_issued"] = document_data.date_issued
    if document_data.owner_department is not None:
        update_data["owner_department"] = document_data.owner_department
    if document_data.status is not None:
        update_data["status"] = document_data.status
    if document_data.is_visible_to_users is not None:
        update_data["is_visible_to_users"] = document_data.is_visible_to_users
    if document_data.visible_to_groups is not None:
        update_data["visible_to_groups"] = document_data.visible_to_groups
    if document_data.description is not None:
        update_data["description"] = document_data.description
    if document_data.tags is not None:
        update_data["tags"] = document_data.tags
    
    # Update document
    result = await db.documents.update_one({"id": document_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Return updated document
    updated_doc = await db.documents.find_one({"id": document_id})
    updated_doc.pop('_id', None)
    return Document(**updated_doc)

@api_router.patch("/documents/{document_id}/visibility")
async def toggle_document_visibility(
    document_id: str, 
    visibility_data: dict,
    current_user: User = Depends(require_admin_or_manager)
):
    update_data = {}
    if "is_visible_to_users" in visibility_data:
        update_data["is_visible_to_users"] = visibility_data["is_visible_to_users"]
    if "visible_to_groups" in visibility_data:
        update_data["visible_to_groups"] = visibility_data["visible_to_groups"]
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No visibility data provided")
    
    result = await db.documents.update_one(
        {"id": document_id}, 
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document visibility updated successfully"}

@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.documents.update_one(
        {"id": document_id},
        {"$set": {"status": "deleted"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

@api_router.patch("/documents/{document_id}/restore")
async def restore_document(document_id: str, current_user: User = Depends(require_admin_or_manager)):
    result = await db.documents.update_one(
        {"id": document_id},
        {"$set": {"status": "active"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document restored successfully"}

@api_router.get("/documents/{document_id}/download")
async def download_document(document_id: str, current_user: User = Depends(get_current_user)):
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.POLICY_MANAGER]:
        if (document.get("status") not in ["active", "archived"] or
            (not document.get("is_visible_to_users", False) and 
             not any(group in current_user.user_group_ids for group in document.get("visible_to_groups", [])))):
            raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = ROOT_DIR / document["file_url"].lstrip('/')
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=document["file_name"],
        media_type='application/octet-stream'
    )

# Update user group assignment
@api_router.patch("/users/{user_id}/groups")
async def update_user_groups(user_id: str, group_ids: List[str], current_user: User = Depends(require_admin)):
    # Verify all group IDs exist
    for group_id in group_ids:
        group = await db.user_groups.find_one({"id": group_id, "is_deleted": False, "is_active": True})
        if not group:
            raise HTTPException(status_code=404, detail=f"User group {group_id} not found")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"user_group_ids": group_ids}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User groups updated successfully"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_default_data()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()