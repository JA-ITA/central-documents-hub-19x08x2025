# AI Prompts for Phased Document Repository Development

## Overview
These prompts are designed to build a document repository system in 5 independent phases, each consumable within 6 credits and buildable without dependencies on future phases.

---

# PHASE 1: Core Backend Foundation & Database

## 🎯 Objective
Build the backend foundation with database models, basic API structure, and file handling. This phase creates a working API that can be tested independently.

## 📋 AI Prompt for Phase 1

```
Create a FastAPI backend for a document repository system with the following requirements:

TECHNICAL STACK:
- FastAPI with async/await
- MongoDB with Motor (async driver) 
- JWT authentication
- File upload handling
- Python 3.9+

DATABASE MODELS (Use UUIDs, not ObjectIDs):
1. Users: id(uuid), username, email, full_name, role(admin/policy_manager/user), is_approved(bool), is_active(bool), is_suspended(bool), is_deleted(bool), password_hash, created_at
2. Categories: id(uuid), name, code(uppercase), description, is_active(bool), is_deleted(bool), created_at  
3. PolicyTypes: id(uuid), name, code(uppercase), description, is_active(bool), is_deleted(bool), created_at
4. Policies: id(uuid), policy_number, title, category_id, policy_type_id, date_issued, version(int), status(active/archived/hidden/deleted), owner_department, file_url, file_name, is_visible_to_users(bool), created_by, created_at, modified_by, modified_at

CORE API ENDPOINTS TO IMPLEMENT:
- POST /api/auth/login (username/password → JWT token)
- POST /api/auth/register (create new user, requires approval)
- GET /api/auth/me (get current user info)
- GET /api/categories (list categories)
- POST /api/categories (create category)
- GET /api/policy-types (list policy types)
- POST /api/policy-types (create policy type)
- POST /api/policies (create policy with file upload)
- GET /api/policies (list policies with filtering)

IMPLEMENTATION REQUIREMENTS:
1. Use environment variables for MongoDB connection and JWT secret
2. Create /uploads directory for file storage
3. Support PDF and DOCX file uploads only
4. Generate policy numbers: CATEGORY-TYPE-001-YYYY-v1 format
5. Hash passwords with bcrypt
6. Implement proper error handling and validation
7. Add CORS middleware for frontend integration

DEFAULT DATA TO CREATE:
- Admin user: username="admin", password="admin123"
- Categories: Operations(OPS), HR(HR), IT(IT)  
- Policy Types: Policy(P), Procedure(PR), Guideline(G)

FILE STRUCTURE:
- server.py (main FastAPI app)
- requirements.txt (dependencies)
- .env (environment variables)
- uploads/ (directory for files)

TESTING REQUIREMENTS:
- All endpoints should return proper HTTP status codes
- File upload should validate file types
- Authentication should work with JWT tokens
- Database operations should handle errors gracefully

SUCCESS CRITERIA:
- Can login with admin credentials
- Can create categories and policy types
- Can upload a document policy
- All endpoints return valid JSON responses
- No errors in server logs

IMPORTANT: This is Phase 1 only. Do not implement public endpoints or advanced features yet. Focus on core CRUD operations and authentication.
```

**Estimated Credits: 4-5 credits**
**Dependencies: None**
**Testing: Use curl commands to test all endpoints**

---

# PHASE 2: Basic Frontend & Authentication Flow

## 🎯 Objective  
Create a React frontend with authentication, basic routing, and admin login functionality. This phase provides a working UI for the backend created in Phase 1.

## 📋 AI Prompt for Phase 2

```
Create a React frontend for the document repository system that connects to the existing FastAPI backend from Phase 1.

TECHNICAL STACK:
- React 18+ with hooks and context
- React Router for navigation
- Axios for API calls
- Tailwind CSS for styling
- Modern component patterns

AUTHENTICATION SYSTEM:
1. Create AuthContext for managing user state and JWT tokens
2. Store tokens in localStorage with automatic header injection
3. Implement login/logout functionality
4. Create ProtectedRoute component for authenticated pages

COMPONENTS TO CREATE:
1. Login Component:
   - Username/password form
   - Login and registration modes
   - Error handling and success messages
   - Clean, professional styling

2. Header Component:
   - User info display (name, role)
   - Logout button
   - Navigation elements

3. Basic Dashboard Component:
   - Welcome message
   - User role display
   - Placeholder for future features

ROUTING STRUCTURE:
- / (redirect to /login if not authenticated, /dashboard if authenticated)
- /login (Login component)
- /dashboard (Dashboard component - protected route)

ENVIRONMENT SETUP:
- Create .env file with REACT_APP_BACKEND_URL
- Configure axios defaults for API base URL
- Set up proper error handling for API calls

STYLING REQUIREMENTS:
- Use Tailwind CSS for consistent styling
- Responsive design (mobile and desktop)
- Professional appearance suitable for corporate use
- Clean forms with proper validation states

AUTHENTICATION FLOW:
1. User enters credentials → POST /api/auth/login
2. Store JWT token and user data in localStorage  
3. Set Authorization header for all future requests
4. Redirect to dashboard on successful login
5. Handle token expiration gracefully

VALIDATION & ERROR HANDLING:
- Form validation (required fields, email format)
- API error display (network errors, invalid credentials)
- Loading states during API calls
- Success messages for actions

FILE STRUCTURE:
- src/App.js (main app with routing)
- src/components/Auth/Login.js
- src/components/Layout/Header.js  
- src/components/Dashboard/Dashboard.js
- src/context/AuthContext.js
- src/utils/api.js (axios configuration)
- package.json with all dependencies

TESTING REQUIREMENTS:
- Login form should connect to backend successfully
- Protected routes should redirect to login when not authenticated
- Token should persist across browser refresh
- Logout should clear authentication state

SUCCESS CRITERIA:
- Can login with admin credentials from Phase 1
- Dashboard loads after successful authentication
- Logout functionality works correctly
- Responsive design works on mobile and desktop
- No console errors in browser

IMPORTANT: This connects to Phase 1 backend. Do not implement document browsing or public access yet. Focus on authentication flow and basic admin interface.
```

**Estimated Credits: 5-6 credits**
**Dependencies: Phase 1 backend must be completed**
**Testing: Manual testing in browser with admin login**

---

# PHASE 3: Public API & Public Document Interface

## 🎯 Objective
Add public endpoints to the backend and create a public document browsing interface that requires no authentication.

## 📋 AI Prompt for Phase 3

```
Extend the existing FastAPI backend and React frontend to add public document access functionality.

BACKEND EXTENSIONS (server.py):

NEW PUBLIC ENDPOINTS (No Authentication Required):
1. GET /api/public/policies
   - Query params: search(string), category_id(string), status(string)
   - Filter: is_visible_to_users=true AND status IN ['active','archived']
   - Return: List of visible policies with category/type names
   - Search: title, policy_number, owner_department (case-insensitive)

2. GET /api/public/policies/{policy_id}
   - Return: Single policy if visible to users
   - 404 if hidden/deleted/not found

3. GET /api/public/policies/{policy_id}/download
   - Return: FileResponse for visible policy documents
   - 404 if hidden/deleted/not found

4. GET /api/public/categories
   - Return: Active, non-deleted categories only

5. GET /api/public/policy-types  
   - Return: Active, non-deleted policy types only

SECURITY REQUIREMENTS:
- Public endpoints must validate visibility before returning data
- No authentication required for public endpoints
- Proper 404 responses for protected content
- Input validation on all query parameters

FRONTEND EXTENSIONS:

NEW COMPONENTS:
1. PublicLayout Component:
   - Header with site title and "Admin Login" button
   - Document browsing interface
   - Search bar with real-time filtering
   - Category and status dropdowns
   - Results table with view/download actions

2. DocumentList Component:
   - Responsive table showing: Document Number, Title, Category, Type, Department, Version, Status
   - View button (eye icon) for each document
   - Download button for each document  
   - Empty state when no documents found

3. SearchFilters Component:
   - Text search input
   - Category dropdown (populated from API)
   - Status dropdown (Active, Archived)
   - Search button to trigger filtering

NEW ROUTING:
- Update App.js to add public routes:
  - / (Public document list - no auth required)
  - /admin-login (Existing login, renamed from /login)
  - /admin (Protected admin dashboard)

API INTEGRATION:
- Create api/public.js for public endpoint calls
- Implement search with debouncing
- Handle loading states and errors
- Cache category/type data to reduce API calls

STYLING UPDATES:
- Professional public-facing design
- Clear distinction between public and admin interfaces
- Responsive table design for mobile devices
- Loading spinners and error messages
- "No documents found" empty states

USER EXPERIENCE:
- Fast search with 300ms debounce
- Clear filtering options
- Intuitive navigation between public and admin areas
- Download files with proper filenames
- Error handling for failed downloads

IMPLEMENTATION DETAILS:
- Use existing authentication system for admin routes
- Public routes bypass authentication entirely
- Maintain existing admin functionality without changes
- Add public API calls alongside existing authenticated calls

SUCCESS CRITERIA:
- Public users can browse visible documents without login
- Search and filtering work correctly
- Download functionality works for visible documents
- Admin login still works (existing functionality preserved)
- Hidden/deleted documents not accessible via public routes
- Mobile-friendly responsive design

TESTING REQUIREMENTS:
- Test public endpoints without authentication headers
- Verify hidden documents return 404 on public endpoints
- Test search functionality with various terms
- Test filtering by category and status
- Verify admin routes still require authentication

IMPORTANT: This extends Phases 1 and 2. Do not modify existing authenticated functionality. Focus on adding parallel public access while preserving all admin features.
```

**Estimated Credits: 6 credits**
**Dependencies: Phases 1 and 2 must be completed**
**Testing: Test both public access (no auth) and admin access (with auth)**

---

# PHASE 4: Admin Dashboard & Document Management

## 🎯 Objective
Build comprehensive admin dashboard with full CRUD operations for documents, categories, users, and policy types.

## 📋 AI Prompt for Phase 4

```
Extend the existing React frontend to create a comprehensive admin dashboard with full document management capabilities.

ADMIN DASHBOARD FEATURES:

TAB-BASED INTERFACE:
1. Policies Tab - Document management
2. Categories Tab - Category CRUD
3. Policy Types Tab - Policy type CRUD  
4. Users Tab - User management (admin only)
5. Upload Tab - New document upload

POLICIES MANAGEMENT:
- Data table with columns: Policy Number, Title, Category, Type, Version, Status, Visibility, Actions
- Search functionality (title, policy number)
- Filter by category, status, visibility
- Admin toggles: "Show Hidden", "Show Deleted"
- Actions per row: View, Edit, Download, Toggle Visibility, Delete/Restore
- Bulk operations support

CATEGORIES MANAGEMENT:
- List all categories with edit/delete options
- Create new category form (name, code, description)
- Soft delete with restore functionality
- Show deleted toggle for admins

POLICY TYPES MANAGEMENT:  
- List all policy types with edit/delete options
- Create new policy type form (name, code, description)
- Activate/deactivate functionality
- Soft delete with restore functionality

USER MANAGEMENT (Admin Only):
- Pending approvals section (approve new user registrations)
- User list with roles: Admin, Policy Manager, User
- User actions: Approve, Suspend, Delete, Restore, Change Role
- Status indicators: Active, Suspended, Deleted

DOCUMENT UPLOAD:
- Multi-step form: Document info → File upload → Review → Submit
- Form fields: Title, Category, Policy Type, Department, Date Issued, Change Summary
- File upload with drag-and-drop support
- File validation (PDF/DOCX only, size limits)
- Progress indicator during upload

ADVANCED FEATURES:
- Document version history display
- Document replacement functionality (with version increment)
- Bulk status changes
- Export functionality (document list as CSV)
- Admin activity logging

BACKEND ENDPOINTS TO ADD:
- PATCH /api/categories/{id} (update category)
- DELETE /api/categories/{id} (soft delete)
- PATCH /api/categories/{id}/restore
- PATCH /api/policy-types/{id} (update policy type)
- DELETE /api/policy-types/{id} (soft delete)  
- PATCH /api/policy-types/{id}/restore
- GET /api/users (admin only)
- PATCH /api/users/{id}/approve
- PATCH /api/users/{id}/suspend
- DELETE /api/users/{id} (soft delete)
- PATCH /api/users/{id}/restore
- PATCH /api/users/{id}/role
- PATCH /api/policies/{id}/visibility
- DELETE /api/policies/{id} (soft delete)
- PATCH /api/policies/{id}/restore

COMPONENT STRUCTURE:
```
src/components/Admin/
├── Dashboard.js (main tabbed interface)
├── Policies/
│   ├── PoliciesList.js
│   ├── PolicyFilters.js  
│   └── PolicyActions.js
├── Categories/
│   ├── CategoriesList.js
│   └── CategoryForm.js
├── PolicyTypes/
│   ├── PolicyTypesList.js
│   └── PolicyTypeForm.js
├── Users/
│   ├── UsersList.js
│   ├── PendingApprovals.js
│   └── UserActions.js
└── Upload/
    ├── UploadForm.js
    └── FileUpload.js
```

UI/UX REQUIREMENTS:
- Tabbed navigation with active state indicators
- Data tables with sorting and pagination
- Inline editing where appropriate
- Confirmation dialogs for destructive actions
- Toast notifications for success/error messages
- Loading states for all async operations
- Responsive design for tablet and desktop use

PERMISSIONS SYSTEM:
- Admin: Full access to all tabs and operations
- Policy Manager: Access to Policies, Categories, Policy Types, Upload
- User: Read-only access (should redirect to public interface)

STATE MANAGEMENT:
- Use React Context for user permissions
- Local state for table filters and pagination
- Proper error boundaries for component failures
- Optimistic updates where appropriate

SUCCESS CRITERIA:
- Admin can perform all CRUD operations on documents, categories, policy types
- User management works (approve, suspend, role changes)
- File upload works with proper validation
- All existing functionality (public access, authentication) continues to work
- Responsive design works on tablets and desktops
- No performance issues with 100+ documents

TESTING REQUIREMENTS:
- Test all CRUD operations
- Test user role restrictions
- Test file upload with various file types
- Test bulk operations
- Verify existing public interface still works

IMPORTANT: This extends Phases 1-3. Ensure all existing public and authentication functionality continues to work. This phase focuses on admin management capabilities only.
```

**Estimated Credits: 6 credits**
**Dependencies: Phases 1, 2, and 3 must be completed**
**Testing: Test admin functionality while ensuring public interface still works**

---

# PHASE 5: PDF Viewer & Intranet Integration

## 🎯 Objective
Add PDF viewing capabilities and prepare the system for intranet integration with embeddable components and configuration options.

## 📋 AI Prompt for Phase 5

```
Add PDF viewing capabilities and intranet integration features to the existing document repository system.

PDF VIEWER IMPLEMENTATION:

INSTALL DEPENDENCIES:
- react-pdf for PDF rendering
- Download PDF.js worker file locally to avoid CORS issues

PDF VIEWER COMPONENTS:
1. PublicPDFViewer (for /document/{id} route):
   - Full-page PDF display with navigation
   - Zoom controls (50% to 200%)
   - Page navigation (previous/next, page X of Y)
   - Print functionality (window.print())
   - Download button
   - Back to documents navigation
   - Mobile-responsive design

2. AdminPDFViewer (for /admin/document/{id} route):
   - Same features as public viewer
   - Additional admin controls (edit document, version history)
   - Admin header with navigation

PDF VIEWER FEATURES:
- Loading states with spinners
- Error handling for corrupted files
- Keyboard navigation (arrow keys for pages)
- Touch gestures for mobile (swipe for pages)
- Print-friendly CSS (hide controls when printing)

ROUTES TO ADD:
- /document/{policy_id} (Public PDF viewer)
- /admin/document/{policy_id} (Admin PDF viewer)

INTRANET INTEGRATION FEATURES:

EMBEDDABLE WIDGET:
1. Create EmbeddableWidget component:
   - Configurable via props: theme, size, features
   - CSS-in-JS to avoid style conflicts
   - Minimal external dependencies
   - Event callbacks for parent integration

2. Widget Configuration Options:
```javascript
const widgetConfig = {
  mode: 'full-page' | 'compact' | 'search-only',
  theme: {
    primaryColor: '#1e40af',
    backgroundColor: '#ffffff', 
    textColor: '#1e293b'
  },
  features: {
    showSearch: true,
    showFilters: true,
    showCategories: ['ops', 'hr'],
    maxResults: 10
  },
  layout: {
    height: '400px',
    showHeader: false,
    compactMode: true
  }
}
```

IFRAME INTEGRATION:
- Add /embed route that accepts query parameters for configuration
- Remove navigation and external links in embedded mode
- PostMessage API for communication with parent window
- CSP headers that allow iframe embedding

WIDGET MODES:
1. Full Page Mode: Complete document repository
2. Compact Mode: Minimal document list with search
3. Search Only Mode: Just search bar and results
4. Category Specific: Documents from specific categories only

CONFIGURATION ENDPOINT:
- GET /api/config (return system configuration for embedding)
- Configurable title, logo, theme colors
- Feature toggles (search, categories, download)

STYLING ISOLATION:
- Use CSS modules or styled-components
- Namespace all CSS classes
- Reset/normalize styles within widget scope
- Responsive breakpoints for various container sizes

INTEGRATION DOCUMENTATION:
Create integration examples:
1. Iframe Integration:
```html
<iframe src="/embed?mode=compact&categories=hr,ops&height=400" 
        width="100%" height="400"></iframe>
```

2. JavaScript Widget:
```html
<div id="document-widget"></div>
<script>
  DocumentWidget.init('#document-widget', {
    apiUrl: '/api',
    mode: 'compact',
    theme: { primaryColor: '#blue' }
  });
</script>
```

BACKEND ADDITIONS:
- GET /api/config (widget configuration)
- Header modifications for iframe support
- CORS policy updates for embedding
- Static file serving for widget assets

PERFORMANCE OPTIMIZATIONS:
- Lazy load PDF pages
- Implement virtual scrolling for large document lists
- Cache frequently accessed documents
- Optimize bundle size for widget mode
- Progressive loading for embedded widgets

MOBILE OPTIMIZATIONS:
- Touch-friendly controls
- Responsive PDF viewer
- Swipe gestures for page navigation  
- Optimized loading for mobile networks

SUCCESS CRITERIA:
- PDF viewer works reliably across browsers
- Documents render correctly with all controls
- Embedded widget works in test iframe
- Configuration options affect widget appearance
- Print functionality works from PDF viewer
- Mobile experience is smooth and responsive
- All existing functionality (public access, admin) continues to work

TESTING REQUIREMENTS:
- Test PDF viewing with real PDF documents
- Test embedding in different container sizes
- Test print functionality
- Test mobile responsiveness
- Verify widget isolation (no CSS conflicts)
- Test with various PDF file sizes and types

BROWSER COMPATIBILITY:
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Mobile Safari and Chrome
- Test PDF.js worker in all target browsers

IMPORTANT: This is the final phase that completes the system. Ensure all previous phases continue to work. Focus on PDF viewing and embedding capabilities while maintaining system stability.
```

**Estimated Credits: 6 credits**
**Dependencies: Phases 1, 2, 3, and 4 must be completed**
**Testing: Test PDF viewing, embedding, and complete system functionality**

---

# 🚀 Phase Execution Guide

## Credit Optimization Tips
1. **Focus on requirements only** - don't add extra features
2. **Use existing libraries** - don't rebuild common functionality
3. **Copy-paste code patterns** - reuse similar implementations
4. **Test incrementally** - verify each component works before proceeding
5. **Document issues clearly** - help AI understand what to fix

## Phase Independence Verification

**After each phase, verify:**
- [ ] Application starts without errors
- [ ] Previous phase functionality still works
- [ ] New features are accessible and functional
- [ ] No broken API endpoints
- [ ] Database migrations (if any) complete successfully

## Inter-Phase Testing Commands

**Phase 1 Testing:**
```bash
curl -X POST localhost:8000/api/auth/login -d '{"username":"admin","password":"admin123"}'
curl -X GET localhost:8000/api/categories -H "Authorization: Bearer <token>"
```

**Phase 2 Testing:**
- Visit frontend URL
- Login with admin credentials
- Verify navigation works

**Phase 3 Testing:**
```bash
curl -X GET localhost:8000/api/public/policies
curl -X GET localhost:3000/ # Should show public interface
```

**Phase 4 Testing:**
- Login as admin
- Test each tab in dashboard
- Create/edit/delete test records

**Phase 5 Testing:**
- Upload a real PDF document
- Test PDF viewer functionality
- Test embedded widget

## Rollback Strategy
If any phase fails:
1. **Revert to previous working state**
2. **Identify specific failing component**
3. **Re-run phase with additional context about the failure**
4. **Test each component individually**

## Success Metrics Per Phase
- **Phase 1:** All API endpoints return 200/201/404 as expected
- **Phase 2:** Can login and see dashboard
- **Phase 3:** Public interface loads and shows documents
- **Phase 4:** Can perform CRUD operations on all entities
- **Phase 5:** Can view PDFs and embed widget works

Each prompt is designed to be self-contained and efficient, building upon the previous phase while ensuring the application remains functional at each step.