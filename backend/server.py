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
# import aiofiles
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

class PolicyType(str, Enum):
    POLICY = "policy"
    PROCEDURE = "procedure"
    GUIDELINE = "guideline"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: UserRole = UserRole.USER
    is_approved: bool = False
    is_active: bool = True
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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CategoryCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""
    parent_id: Optional[str] = None

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
    policy_type: PolicyType
    date_issued: datetime
    version: int = 1
    status: PolicyStatus = PolicyStatus.ACTIVE
    owner_department: str
    file_url: str
    file_name: str
    version_history: List[PolicyVersion] = []
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None

class PolicyCreate(BaseModel):
    title: str
    category_id: str
    policy_type: PolicyType
    date_issued: datetime
    owner_department: str
    policy_number: Optional[str] = None

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[str] = None
    policy_type: Optional[PolicyType] = None
    date_issued: Optional[datetime] = None
    owner_department: Optional[str] = None
    status: Optional[PolicyStatus] = None

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
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
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

async def generate_policy_number(category_id: str, policy_type: PolicyType, year: int) -> str:
    # Get category
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_code = category["code"]
    type_code = policy_type.value[0].upper()  # P, PR, G for Policy, Procedure, Guideline
    
    # Get next sequential number for this category and year
    existing_policies = await db.policies.find({
        "category_id": category_id,
        "date_issued": {
            "$gte": datetime(year, 1, 1),
            "$lt": datetime(year + 1, 1, 1)
        }
    }).to_list(None)
    
    next_seq = len(existing_policies) + 1
    
    return f"{category_code}-{type_code}-{next_seq:03d}-{year}-v1"

# Initialize default data
async def init_default_data():
    # Check if admin user exists
    admin_exists = await db.users.find_one({"role": UserRole.ADMIN})
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
    ops_category = await db.categories.find_one({"code": "OPS"})
    if not ops_category:
        default_category = Category(
            name="Operations",
            code="OPS",
            description="Operational policies and procedures"
        )
        await db.categories.insert_one(default_category.dict())
        print("Default Operations category created")

# Authentication Routes
@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = await db.users.find_one({"email": user_data.email})
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
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user["is_approved"] or not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account not approved or inactive")
    
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

# Category Routes
@api_router.post("/categories", response_model=Category)
async def create_category(category_data: CategoryCreate, current_user: User = Depends(require_admin_or_manager)):
    category = Category(**category_data.dict())
    await db.categories.insert_one(category.dict())
    return category

@api_router.get("/categories", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await db.categories.find().to_list(None)
    return [Category(**cat) for cat in categories]

# Policy Routes
@api_router.post("/policies")
async def create_policy(
    title: str = Form(...),
    category_id: str = Form(...),
    policy_type: PolicyType = Form(...),
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
        policy_number = await generate_policy_number(category_id, policy_type, issued_date.year)
    
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
        policy_type=policy_type,
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
    current_user: User = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if category_id:
        query["category_id"] = category_id
    
    policies = await db.policies.find(query).to_list(None)
    return [Policy(**policy) for policy in policies]

@api_router.get("/policies/{policy_id}", response_model=Policy)
async def get_policy(policy_id: str, current_user: User = Depends(get_current_user)):
    policy = await db.policies.find_one({"id": policy_id})
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return Policy(**policy)

@api_router.get("/policies/{policy_id}/download")
async def download_policy(policy_id: str, current_user: User = Depends(get_current_user)):
    policy = await db.policies.find_one({"id": policy_id})
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

# User Management Routes
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_admin)):
    users = await db.users.find().to_list(None)
    result = []
    for user in users:
        user_dict = user.copy()
        user_dict.pop('password_hash', None)
        result.append(User(**user_dict, password_hash=""))
    return result

@api_router.patch("/users/{user_id}/approve")
async def approve_user(user_id: str, current_user: User = Depends(require_admin)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_approved": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User approved successfully"}

@api_router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role: UserRole, current_user: User = Depends(require_admin)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User role updated successfully"}

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