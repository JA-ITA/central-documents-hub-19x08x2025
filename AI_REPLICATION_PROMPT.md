# AI Document Repository Replication Prompt

## System Overview
Create a full-stack document repository system that allows public access to documents while maintaining administrative controls. The system should be suitable for intranet integration and provide both public viewing and administrative management capabilities.

## Core Requirements

### 1. Architecture & Tech Stack
- **Backend**: FastAPI (Python) with async/await patterns
- **Frontend**: React 18+ with modern hooks and routing
- **Database**: MongoDB with UUID-based document IDs
- **File Storage**: Local file system with organized upload structure
- **Authentication**: JWT-based auth for admin functions only

### 2. Database Schema

#### Users Collection
```javascript
{
  id: "uuid4",
  username: "string",
  email: "string", 
  full_name: "string",
  role: "admin|policy_manager|user",
  is_approved: boolean,
  is_active: boolean,
  is_suspended: boolean,
  is_deleted: boolean,
  created_at: datetime,
  password_hash: "bcrypt_hash"
}
```

#### Categories Collection
```javascript
{
  id: "uuid4",
  name: "string",
  code: "string (uppercase)",
  description: "string",
  parent_id: "string (optional)",
  is_active: boolean,
  is_deleted: boolean,
  created_at: datetime
}
```

#### Policy Types Collection
```javascript
{
  id: "uuid4", 
  name: "string",
  code: "string (uppercase)",
  description: "string",
  is_active: boolean,
  is_deleted: boolean,
  created_at: datetime
}
```

#### Policies Collection (Documents)
```javascript
{
  id: "uuid4",
  policy_number: "string (auto-generated: CAT-TYPE-001-YYYY-v1)",
  title: "string",
  category_id: "string (foreign key)",
  policy_type_id: "string (foreign key)", 
  date_issued: datetime,
  version: integer,
  status: "active|archived|hidden|deleted",
  owner_department: "string",
  file_url: "string (/uploads/filename)",
  file_name: "string",
  is_visible_to_users: boolean,
  version_history: [
    {
      version_number: integer,
      upload_date: datetime,
      uploaded_by: "string",
      change_summary: "string",
      file_url: "string",
      file_name: "string"
    }
  ],
  created_by: "string",
  created_at: datetime,
  modified_by: "string (optional)",
  modified_at: "datetime (optional)"
}
```

### 3. Backend API Endpoints

#### Public Endpoints (No Authentication Required)
```python
GET /api/public/policies
  - Query params: search, category_id, status
  - Returns: List of visible documents only
  - Filter: is_visible_to_users=true AND status IN ['active','archived']

GET /api/public/policies/{policy_id}
  - Returns: Single visible document details
  - 404 if hidden/deleted/not found

GET /api/public/policies/{policy_id}/download  
  - Returns: File download for visible documents
  - 404 if hidden/deleted/not found

GET /api/public/categories
  - Returns: Active, non-deleted categories only

GET /api/public/policy-types
  - Returns: Active, non-deleted policy types only
```

#### Admin Endpoints (Authentication Required)
```python
POST /api/auth/login
POST /api/auth/register  
GET /api/auth/me

# Document Management
GET /api/policies (with admin filters)
POST /api/policies (file upload)
PATCH /api/policies/{id}
DELETE /api/policies/{id} (soft delete)
PATCH /api/policies/{id}/restore
PATCH /api/policies/{id}/visibility?is_visible=boolean
PATCH /api/policies/{id}/document (document replacement)
GET /api/policies/{id}/download

# Category Management  
GET /api/categories?include_deleted=boolean
POST /api/categories
PATCH /api/categories/{id}
DELETE /api/categories/{id}
PATCH /api/categories/{id}/restore

# Policy Type Management
GET /api/policy-types?include_inactive=boolean&include_deleted=boolean
POST /api/policy-types  
PATCH /api/policy-types/{id}
DELETE /api/policy-types/{id}
PATCH /api/policy-types/{id}/restore

# User Management (Admin Only)
GET /api/users?include_deleted=boolean
PATCH /api/users/{id}
PATCH /api/users/{id}/approve
PATCH /api/users/{id}/suspend  
DELETE /api/users/{id}
PATCH /api/users/{id}/restore
PATCH /api/users/{id}/role?role=new_role
```

### 4. Frontend Component Structure

#### Public Components
```jsx
// Main public interface at root path /
const PublicPolicyList = () => {
  // Document list with search/filter
  // Category and status filters
  // View and download actions
  // Admin login button
}

// Document viewer at /document/{id}  
const PublicPDFViewer = () => {
  // PDF.js integration with local worker
  // Zoom, print, download controls
  // Page navigation
  // Back to list navigation
}

// Admin authentication at /admin-login
const AdminLogin = () => {
  // Clean login form
  // Back to public site button
  // Registration option
}
```

#### Admin Components (Authentication Required)
```jsx
// Admin dashboard at /admin
const Dashboard = () => {
  // Tabbed interface: Policies, Categories, Types, Users, Upload
  // Advanced search and filtering
  // Show hidden/deleted toggles
  // CRUD operations for all entities
}

// Admin PDF viewer at /admin/policy/{id}
const PDFViewer = () => {
  // Enhanced viewer with admin controls
  // Document editing capabilities
  // Version history access
}

const DocumentEditDialog = () => {
  // File upload replacement
  // Change summary logging
  // Version increment
}
```

### 5. Routing Configuration
```jsx
<Routes>
  {/* Public Routes - No Authentication */}
  <Route path="/" element={<PublicPolicyList />} />
  <Route path="/document/:policyId" element={<PublicPDFViewer />} />
  
  {/* Admin Routes - Authentication Required */}
  <Route path="/admin-login" element={<AdminLogin />} />
  <Route path="/admin" element={<Dashboard />} />
  <Route path="/admin/policy/:policyId" element={<PDFViewer />} />
</Routes>
```

### 6. Key Implementation Details

#### PDF.js Integration
- Download local PDF.js worker to public/pdf.worker.min.js
- Set worker source: `pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js'`
- Handle PDF loading errors gracefully
- Implement zoom (0.5x to 2.0x), page navigation, print functionality

#### File Upload Handling
- Support PDF and DOCX file types only
- Validate file extensions on frontend and backend
- Use FormData for multipart uploads
- Generate unique filenames: `{policy_number}_v{version}.{extension}`
- Store in organized upload directory structure

#### Security Implementation
- JWT tokens for admin authentication
- Role-based access control (admin, policy_manager, user)
- Public endpoints have no authentication requirements
- File access validation before serving downloads
- Input sanitization and validation

#### Search and Filtering
```python
# Backend search implementation
query = {}
if search_term:
    query["$or"] = [
        {"title": {"$regex": search_term, "$options": "i"}},
        {"policy_number": {"$regex": search_term, "$options": "i"}}, 
        {"owner_department": {"$regex": search_term, "$options": "i"}}
    ]
if category_id:
    query["category_id"] = category_id
if status:
    query["status"] = status
```

#### Default Data Setup
```python
# Initialize on startup
default_admin = {
  "username": "admin",
  "password": "admin123",  
  "email": "admin@company.com",
  "role": "admin",
  "is_approved": True
}

default_categories = [
  {"name": "Operations", "code": "OPS"},
  {"name": "Human Resources", "code": "HR"}, 
  {"name": "Information Technology", "code": "IT"}
]

default_policy_types = [
  {"name": "Policy", "code": "P"},
  {"name": "Procedure", "code": "PR"},
  {"name": "Guideline", "code": "G"}
]
```

### 7. Environment Configuration

#### Backend .env
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=document_repository
CORS_ORIGINS=*
```

#### Frontend .env  
```
REACT_APP_BACKEND_URL=https://your-domain.com
WDS_SOCKET_PORT=443
```

### 8. Styling and UI Framework
- Use Tailwind CSS for consistent styling
- Implement shadcn/ui components for consistent UI elements
- Responsive design for mobile and desktop
- Clean, professional appearance suitable for corporate environments

### 9. Deployment Considerations
- Containerized with Docker for easy deployment
- Supervisor for process management
- MongoDB with proper indexing for search performance
- File storage with backup strategies
- Health check endpoints for monitoring

### 10. Testing Requirements
- Public API endpoints should work without authentication
- Admin API endpoints should require valid JWT tokens
- File upload/download functionality should handle various file types
- Search and filtering should be case-insensitive and performant
- PDF viewer should handle CORS issues properly

## Implementation Priority
1. **Core Backend**: Database models, authentication, API endpoints
2. **Public Frontend**: Document browsing, PDF viewer, search/filter
3. **Admin Frontend**: Dashboard, CRUD operations, file management
4. **Integration Features**: Embedding support, theming options
5. **Advanced Features**: Full-text search, analytics, workflow management

## Success Criteria
- Public users can browse and download visible documents without authentication
- Admin users can manage all documents, categories, and users after authentication  
- System is performant with 100+ documents
- PDF viewing works reliably across browsers
- Code is well-organized and maintainable for future enhancements

## Additional Implementation Notes
- Use async/await patterns throughout for better performance
- Implement proper error handling and user feedback
- Add loading states for better user experience
- Consider accessibility requirements (WCAG 2.1)
- Implement proper logging for debugging and monitoring
- Use environment variables for all configuration
- Follow RESTful API design principles
- Implement proper data validation on both frontend and backend

This prompt provides a comprehensive blueprint for recreating the document repository system with all necessary technical details, database schemas, API specifications, and implementation guidance.