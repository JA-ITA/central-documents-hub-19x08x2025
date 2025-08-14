import React, { useState, useEffect, useContext, createContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Label } from './components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Separator } from './components/ui/separator';
import { Alert, AlertDescription } from './components/ui/alert';
import { Switch } from './components/ui/switch';
import { 
  FileText, 
  Users, 
  FolderOpen, 
  Upload, 
  Download, 
  Eye, 
  Shield, 
  Settings,
  Plus,
  CheckCircle,
  XCircle,
  Search,
  Filter,
  LogOut,
  User,
  EyeOff,
  Trash2,
  RefreshCw,
  UserX,
  UserCheck,
  Edit,
  Archive,
  ArrowLeft,
  Printer,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import './App.css';

// Set up PDF.js worker - use jsdelivr CDN as fallback
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      setUser(JSON.parse(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      await axios.post(`${API}/auth/register`, userData);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (isLogin) {
      const result = await login(formData.username, formData.password);
      if (!result.success) {
        setError(result.error);
      }
    } else {
      const result = await register(formData);
      if (result.success) {
        setSuccess('Registration successful! Please wait for admin approval.');
        setIsLogin(true);
        setFormData({ username: '', password: '', email: '', full_name: '' });
      } else {
        setError(result.error);
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold text-slate-800">
            Central Policy Register
          </CardTitle>
          <CardDescription className="text-slate-600">
            {isLogin ? 'Sign in to your account' : 'Create a new account'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                required
              />
            </div>

            {!isLogin && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input
                    id="full_name"
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>

            {error && (
              <Alert className="border-red-200 bg-red-50">
                <XCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-700">{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-700">{success}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full bg-slate-800 hover:bg-slate-700">
              {isLogin ? 'Sign In' : 'Sign Up'}
            </Button>
          </form>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-slate-600 hover:text-slate-800"
            >
              {isLogin ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
            </button>
          </div>


        </CardContent>
      </Card>
    </div>
  );
};

// PDF Viewer Component
const PDFViewer = () => {
  const { policyId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [policy, setPolicy] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPolicy();
  }, [policyId]);

  const fetchPolicy = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/policies/${policyId}`);
      setPolicy(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching policy:', error);
      setError('Failed to load policy document');
    } finally {
      setLoading(false);
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = async () => {
    try {
      const response = await axios.get(`${API}/policies/${policyId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', policy.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading policy:', error);
    }
  };

  const changePage = (offset) => {
    setPageNumber(prevPageNumber => prevPageNumber + offset);
  };

  const previousPage = () => {
    changePage(-1);
  };

  const nextPage = () => {
    changePage(1);
  };

  const zoomIn = () => {
    setScale(prevScale => Math.min(prevScale + 0.1, 2.0));
  };

  const zoomOut = () => {
    setScale(prevScale => Math.max(prevScale - 0.1, 0.5));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto"></div>
          <p className="mt-2 text-slate-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error || !policy) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Document</h3>
            <p className="text-slate-600 mb-4">{error}</p>
            <Button onClick={() => navigate('/')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const pdfUrl = `${BACKEND_URL}${policy.file_url}`;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm print:hidden">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={() => navigate('/')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
              <Separator orientation="vertical" className="h-6" />
              <div>
                <h1 className="text-xl font-bold text-slate-800">{policy.title}</h1>
                <p className="text-sm text-slate-600">Policy Number: {policy.policy_number}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={zoomOut}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="text-sm text-slate-600 min-w-[60px] text-center">
                {Math.round(scale * 100)}%
              </span>
              <Button variant="outline" size="sm" onClick={zoomIn}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Separator orientation="vertical" className="h-6" />
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button variant="outline" size="sm" onClick={handlePrint}>
                <Printer className="h-4 w-4 mr-2" />
                Print
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* PDF Content */}
      <main className="container mx-auto px-6 py-6">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Navigation Bar */}
          <div className="bg-slate-100 px-4 py-3 flex items-center justify-between border-b print:hidden">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={previousPage}
                disabled={pageNumber <= 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-slate-600">
                Page {pageNumber} of {numPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={nextPage}
                disabled={pageNumber >= numPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            <div className="text-sm text-slate-600">
              Version {policy.version} • {new Date(policy.date_issued).toLocaleDateString()}
            </div>
          </div>

          {/* PDF Document */}
          <div className="pdf-container flex justify-center p-4 bg-slate-50">
            <div className="pdf-document bg-white shadow-lg">
              <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={
                  <div className="flex items-center justify-center h-96">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800"></div>
                  </div>
                }
                error={
                  <div className="flex items-center justify-center h-96 text-red-600">
                    <div className="text-center">
                      <XCircle className="h-12 w-12 mx-auto mb-2" />
                      <p>Failed to load PDF document</p>
                    </div>
                  </div>
                }
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  className="pdf-page"
                />
              </Document>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

// Header Component
const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-slate-800 text-white shadow-lg">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="h-8 w-8" />
            <div>
              <h1 className="text-xl font-bold">Central Policy Register</h1>
              <p className="text-sm text-slate-300">Policy Management System</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="bg-slate-700 text-white border-slate-600">
              {user?.role?.replace('_', ' ').toUpperCase()}
            </Badge>
            <div className="flex items-center space-x-2">
              <User className="h-4 w-4" />
              <span className="text-sm">{user?.full_name}</span>
            </div>
            <Button variant="ghost" size="sm" onClick={logout} className="text-slate-300 hover:text-white">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

// Document Edit Dialog Component
const DocumentEditDialog = ({ policy, onUpdate, isOpen, onOpenChange }) => {
  const [file, setFile] = useState(null);
  const [changeSummary, setChangeSummary] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Validate file type
      if (!selectedFile.name.toLowerCase().endsWith('.pdf') && !selectedFile.name.toLowerCase().endsWith('.docx')) {
        setError('Only PDF and DOCX files are allowed');
        return;
      }
      setFile(selectedFile);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('change_summary', changeSummary || 'Document updated');

      await axios.patch(`${API}/policies/${policy.id}/document`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Reset form
      setFile(null);
      setChangeSummary('');
      onOpenChange(false);
      onUpdate();
      
      // Reset file input
      const fileInput = document.getElementById('document-file');
      if (fileInput) fileInput.value = '';
    } catch (error) {
      console.error('Error updating document:', error);
      setError(error.response?.data?.detail || 'Failed to update document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Policy Document</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Current Document</Label>
            <div className="text-sm text-slate-600">
              <p>{policy.file_name}</p>
              <p>Version {policy.version}</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="document-file">New Document *</Label>
            <Input
              id="document-file"
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              required
            />
            <p className="text-sm text-slate-500">Supported formats: PDF, DOCX</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="change-summary">Change Summary</Label>
            <Textarea
              id="change-summary"
              value={changeSummary}
              onChange={(e) => setChangeSummary(e.target.value)}
              placeholder="Describe the changes made to the document..."
              rows={3}
            />
          </div>

          {error && (
            <Alert className="border-red-200 bg-red-50">
              <XCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-700">{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex space-x-2 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={uploading}>
              {uploading ? 'Updating...' : 'Update Document'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [policies, setPolicies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [users, setUsers] = useState([]);
  const [policyTypes, setPolicyTypes] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [showHidden, setShowHidden] = useState(false);
  const [showDeleted, setShowDeleted] = useState(false);
  const [showDeletedPolicyTypes, setShowDeletedPolicyTypes] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  useEffect(() => {
    fetchPolicies();
    fetchCategories();
    fetchPolicyTypes();
    if (user.role === 'admin') {
      fetchUsers();
    }
  }, [user, showHidden, showDeleted, showDeletedPolicyTypes]);

  const fetchPolicies = async () => {
    try {
      const params = new URLSearchParams();
      if (user.role === 'admin') {
        if (showHidden) params.append('include_hidden', 'true');
        if (showDeleted) params.append('include_deleted', 'true');
      }
      const response = await axios.get(`${API}/policies?${params}`);
      setPolicies(response.data);
    } catch (error) {
      console.error('Error fetching policies:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const params = user.role === 'admin' && showDeleted ? '?include_deleted=true' : '';
      const response = await axios.get(`${API}/categories${params}`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchPolicyTypes = async () => {
    try {
      const params = new URLSearchParams();
      if (user.role === 'admin') {
        params.append('include_inactive', 'true');
        if (showDeletedPolicyTypes) params.append('include_deleted', 'true');
      }
      const response = await axios.get(`${API}/policy-types?${params}`);
      setPolicyTypes(response.data);
    } catch (error) {
      console.error('Error fetching policy types:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const params = showDeleted ? '?include_deleted=true' : '';
      const response = await axios.get(`${API}/users${params}`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleDownload = async (policyId) => {
    try {
      const response = await axios.get(`${API}/policies/${policyId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `policy_${policyId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading policy:', error);
    }
  };

  // Policy management functions
  const togglePolicyVisibility = async (policyId, isVisible) => {
    try {
      await axios.patch(`${API}/policies/${policyId}/visibility?is_visible=${!isVisible}`);
      fetchPolicies();
    } catch (error) {
      console.error('Error toggling policy visibility:', error);
    }
  };

  const deletePolicy = async (policyId) => {
    if (window.confirm('Are you sure you want to delete this policy?')) {
      try {
        await axios.delete(`${API}/policies/${policyId}`);
        fetchPolicies();
      } catch (error) {
        console.error('Error deleting policy:', error);
      }
    }
  };

  const restorePolicy = async (policyId) => {
    try {
      await axios.patch(`${API}/policies/${policyId}/restore`);
      fetchPolicies();
    } catch (error) {
      console.error('Error restoring policy:', error);
    }
  };

  // User management functions
  const handleApproveUser = async (userId) => {
    try {
      await axios.patch(`${API}/users/${userId}/approve`);
      fetchUsers();
    } catch (error) {
      console.error('Error approving user:', error);
    }
  };

  const handleSuspendUser = async (userId) => {
    try {
      await axios.patch(`${API}/users/${userId}/suspend`);
      fetchUsers();
    } catch (error) {
      console.error('Error suspending user:', error);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`${API}/users/${userId}`);
        fetchUsers();
      } catch (error) {
        console.error('Error deleting user:', error);
      }
    }
  };

  const handleRestoreUser = async (userId) => {
    try {
      await axios.patch(`${API}/users/${userId}/restore`);
      fetchUsers();
    } catch (error) {
      console.error('Error restoring user:', error);
    }
  };

  const handleChangeUserRole = async (userId, newRole) => {
    try {
      await axios.patch(`${API}/users/${userId}/role?role=${newRole}`);
      fetchUsers();
    } catch (error) {
      console.error('Error changing user role:', error);
    }
  };

  // Category management functions
  const deleteCategory = async (categoryId) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await axios.delete(`${API}/categories/${categoryId}`);
        fetchCategories();
      } catch (error) {
        console.error('Error deleting category:', error);
      }
    }
  };

  const restoreCategory = async (categoryId) => {
    try {
      await axios.patch(`${API}/categories/${categoryId}/restore`);
      fetchCategories();
    } catch (error) {
      console.error('Error restoring category:', error);
    }
  };

  const filteredPolicies = policies.filter(policy => {
    const matchesSearch = policy.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         policy.policy_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || !selectedCategory || policy.category_id === selectedCategory;
    const matchesStatus = selectedStatus === 'all' || !selectedStatus || policy.status === selectedStatus;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Unknown';
  };

  const getPolicyTypeName = (policyTypeId) => {
    const type = policyTypes.find(pt => pt.id === policyTypeId);
    return type ? type.name : 'Unknown';
  };

  const handleEditDocument = (policy) => {
    setEditingPolicy(policy);
    setIsEditDialogOpen(true);
  };

  const handleViewPolicy = (policy) => {
    navigate(`/policy/${policy.id}`);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        <Tabs defaultValue="policies" className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="policies" className="flex items-center space-x-2">
              <FileText className="h-4 w-4" />
              <span>Policies</span>
            </TabsTrigger>
            <TabsTrigger value="categories" className="flex items-center space-x-2">
              <FolderOpen className="h-4 w-4" />
              <span>Categories</span>
            </TabsTrigger>
            <TabsTrigger value="policy-types" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span>Policy Types</span>
            </TabsTrigger>
            {user.role === 'admin' && (
              <TabsTrigger value="users" className="flex items-center space-x-2">
                <Users className="h-4 w-4" />
                <span>Users</span>
              </TabsTrigger>
            )}
            {(user.role === 'admin' || user.role === 'policy_manager') && (
              <TabsTrigger value="upload" className="flex items-center space-x-2">
                <Upload className="h-4 w-4" />
                <span>Upload Policy</span>
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="policies" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Policy Management</CardTitle>
                    <CardDescription>
                      Browse, search, and manage organizational policies
                    </CardDescription>
                  </div>
                  {user.role === 'admin' && (
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <Label htmlFor="show-hidden">Show Hidden</Label>
                        <Switch
                          id="show-hidden"
                          checked={showHidden}
                          onCheckedChange={setShowHidden}
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <Label htmlFor="show-deleted">Show Deleted</Label>
                        <Switch
                          id="show-deleted"
                          checked={showDeleted}
                          onCheckedChange={setShowDeleted}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1">
                    <Label htmlFor="search">Search Policies</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-4 w-4" />
                      <Input
                        id="search"
                        placeholder="Search by title or policy number..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  
                  <div className="md:w-48">
                    <Label htmlFor="category-filter">Category</Label>
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                      <SelectTrigger>
                        <SelectValue placeholder="All Categories" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Categories</SelectItem>
                        {categories.filter(cat => !cat.is_deleted || showDeleted).map(category => (
                          <SelectItem key={category.id} value={category.id}>
                            {category.name} {category.is_deleted && '(Deleted)'}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="md:w-32">
                    <Label htmlFor="status-filter">Status</Label>
                    <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                      <SelectTrigger>
                        <SelectValue placeholder="All Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="archived">Archived</SelectItem>
                        <SelectItem value="hidden">Hidden</SelectItem>
                        <SelectItem value="deleted">Deleted</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Policy Number</TableHead>
                        <TableHead>Title</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Version</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Visibility</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredPolicies.map(policy => (
                        <TableRow key={policy.id}>
                          <TableCell className="font-mono text-sm">
                            {policy.policy_number}
                          </TableCell>
                          <TableCell className="font-medium">
                            {policy.title}
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary">
                              {getCategoryName(policy.category_id)}
                            </Badge>
                          </TableCell>
                          <TableCell className="capitalize">
                            {getPolicyTypeName(policy.policy_type_id)}
                          </TableCell>
                          <TableCell>v{policy.version}</TableCell>
                          <TableCell>
                            <Badge 
                              variant={
                                policy.status === 'active' ? 'default' : 
                                policy.status === 'deleted' ? 'destructive' : 'outline'
                              }
                              className={
                                policy.status === 'active' ? 'bg-green-600' :
                                policy.status === 'deleted' ? 'bg-red-600' : ''
                              }
                            >
                              {policy.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {policy.is_visible_to_users ? (
                              <Eye className="h-4 w-4 text-green-600" />
                            ) : (
                              <EyeOff className="h-4 w-4 text-red-600" />
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleViewPolicy(policy)}
                                className="h-8 px-2"
                                title="View document"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDownload(policy.id)}
                                className="h-8 px-2"
                                title="Download document"
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                              {user.role === 'admin' && (
                                <>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleEditDocument(policy)}
                                    className="h-8 px-2"
                                    title="Edit document"
                                  >
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => togglePolicyVisibility(policy.id, policy.is_visible_to_users)}
                                    className="h-8 px-2"
                                    title={policy.is_visible_to_users ? "Hide from users" : "Show to users"}
                                  >
                                    {policy.is_visible_to_users ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                  </Button>
                                  {policy.status === 'deleted' ? (
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => restorePolicy(policy.id)}
                                      className="h-8 px-2 text-green-600"
                                      title="Restore policy"
                                    >
                                      <RefreshCw className="h-4 w-4" />
                                    </Button>
                                  ) : (
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => deletePolicy(policy.id)}
                                      className="h-8 px-2 text-red-600"
                                      title="Delete policy"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  )}
                                </>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="categories">
            <CategoryManager 
              categories={categories} 
              onUpdate={fetchCategories} 
              showDeleted={showDeleted}
              onShowDeletedChange={setShowDeleted}
              onDelete={deleteCategory}
              onRestore={restoreCategory}
              userRole={user.role}
            />
          </TabsContent>

          <TabsContent value="policy-types">
            <PolicyTypeManager 
              policyTypes={policyTypes} 
              onUpdate={fetchPolicyTypes} 
              userRole={user.role}
              showDeleted={showDeletedPolicyTypes}
              onShowDeletedChange={setShowDeletedPolicyTypes}
            />
          </TabsContent>

          {user.role === 'admin' && (
            <TabsContent value="users">
              <UserManager 
                users={users} 
                onUpdate={fetchUsers}
                showDeleted={showDeleted}
                onShowDeletedChange={setShowDeleted}
                onApprove={handleApproveUser}
                onSuspend={handleSuspendUser}
                onDelete={handleDeleteUser}
                onRestore={handleRestoreUser}
                onChangeRole={handleChangeUserRole}
              />
            </TabsContent>
          )}

          {(user.role === 'admin' || user.role === 'policy_manager') && (
            <TabsContent value="upload">
              <PolicyUploader 
                categories={categories.filter(cat => !cat.is_deleted)} 
                policyTypes={policyTypes.filter(pt => pt.is_active && !pt.is_deleted)}
                onUpload={fetchPolicies} 
              />
            </TabsContent>
          )}
        </Tabs>
      </main>

      {/* Document Edit Dialog */}
      {editingPolicy && (
        <DocumentEditDialog
          policy={editingPolicy}
          onUpdate={fetchPolicies}
          isOpen={isEditDialogOpen}
          onOpenChange={setIsEditDialogOpen}
        />
      )}
    </div>
  );
};

// Enhanced Policy Type Manager Component
const PolicyTypeManager = ({ policyTypes, onUpdate, userRole, showDeleted, onShowDeletedChange }) => {
  const [newPolicyType, setNewPolicyType] = useState({ name: '', code: '', description: '' });
  const [isAddingPolicyType, setIsAddingPolicyType] = useState(false);

  const handleAddPolicyType = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/policy-types`, newPolicyType);
      setNewPolicyType({ name: '', code: '', description: '' });
      setIsAddingPolicyType(false);
      onUpdate();
    } catch (error) {
      console.error('Error adding policy type:', error);
    }
  };

  const togglePolicyType = async (typeId, isActive) => {
    try {
      await axios.patch(`${API}/policy-types/${typeId}`, { is_active: !isActive });
      onUpdate();
    } catch (error) {
      console.error('Error updating policy type:', error);
    }
  };

  const deletePolicyType = async (typeId) => {
    if (window.confirm('Are you sure you want to delete this policy type?')) {
      try {
        await axios.delete(`${API}/policy-types/${typeId}`);
        onUpdate();
      } catch (error) {
        console.error('Error deleting policy type:', error);
      }
    }
  };

  const restorePolicyType = async (typeId) => {
    try {
      await axios.patch(`${API}/policy-types/${typeId}/restore`);
      onUpdate();
    } catch (error) {
      console.error('Error restoring policy type:', error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Policy Type Management</CardTitle>
            <CardDescription>Manage policy types and their status</CardDescription>
          </div>
          <div className="flex items-center space-x-4">
            {userRole === 'admin' && (
              <div className="flex items-center space-x-2">
                <Label htmlFor="show-deleted-types">Show Deleted</Label>
                <Switch
                  id="show-deleted-types"
                  checked={showDeleted}
                  onCheckedChange={onShowDeletedChange}
                />
              </div>
            )}
            {userRole === 'admin' && (
              <Dialog open={isAddingPolicyType} onOpenChange={setIsAddingPolicyType}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Policy Type
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Policy Type</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleAddPolicyType} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="type-name">Name</Label>
                      <Input
                        id="type-name"
                        value={newPolicyType.name}
                        onChange={(e) => setNewPolicyType({...newPolicyType, name: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="type-code">Code</Label>
                      <Input
                        id="type-code"
                        value={newPolicyType.code}
                        onChange={(e) => setNewPolicyType({...newPolicyType, code: e.target.value.toUpperCase()})}
                        placeholder="e.g., P, PR, G"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="type-desc">Description</Label>
                      <Textarea
                        id="type-desc"
                        value={newPolicyType.description}
                        onChange={(e) => setNewPolicyType({...newPolicyType, description: e.target.value})}
                      />
                    </div>
                    <Button type="submit" className="w-full">Add Policy Type</Button>
                  </form>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Code</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Status</TableHead>
                {userRole === 'admin' && <TableHead>Actions</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {policyTypes.map(type => (
                <TableRow key={type.id} className={type.is_deleted ? 'opacity-60 bg-red-50' : ''}>
                  <TableCell className="font-medium">{type.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{type.code}</Badge>
                  </TableCell>
                  <TableCell className="text-sm text-slate-600">{type.description}</TableCell>
                  <TableCell>
                    <div className="flex flex-col space-y-1">
                      <Badge variant={type.is_deleted ? 'destructive' : type.is_active ? 'default' : 'secondary'}>
                        {type.is_deleted ? 'Deleted' : type.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </TableCell>
                  {userRole === 'admin' && (
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {type.is_deleted ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => restorePolicyType(type.id)}
                            className="h-8 px-2 text-green-600"
                            title="Restore policy type"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => togglePolicyType(type.id, type.is_active)}
                              className="h-8 px-2"
                              title={type.is_active ? "Deactivate" : "Activate"}
                            >
                              {type.is_active ? 'Deactivate' : 'Activate'}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deletePolicyType(type.id)}
                              className="h-8 px-2 text-red-600"
                              title="Delete policy type"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

// Enhanced Policy Uploader Component
const PolicyUploader = ({ categories, policyTypes, onUpload }) => {
  const [formData, setFormData] = useState({
    title: '',
    category_id: '',
    policy_type_id: '',
    date_issued: '',
    owner_department: '',
    policy_number: '',
    change_summary: 'Initial version'
  });
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage('Please select a file');
      return;
    }

    setUploading(true);
    try {
      const formDataObj = new FormData();
      Object.keys(formData).forEach(key => {
        formDataObj.append(key, formData[key]);
      });
      formDataObj.append('file', file);

      await axios.post(`${API}/policies`, formDataObj, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setMessage('Policy uploaded successfully!');
      setFormData({
        title: '',
        category_id: '',
        policy_type_id: '',
        date_issued: '',
        owner_department: '',
        policy_number: '',
        change_summary: 'Initial version'
      });
      setFile(null);
      onUpload();
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || 'Upload failed'}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload New Policy</CardTitle>
        <CardDescription>
          Add a new policy document to the system
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category *</Label>
              <Select value={formData.category_id} onValueChange={(value) => setFormData({...formData, category_id: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(category => (
                    <SelectItem key={category.id} value={category.id}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="policy_type">Type *</Label>
              <Select value={formData.policy_type_id} onValueChange={(value) => setFormData({...formData, policy_type_id: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {policyTypes.map(type => (
                    <SelectItem key={type.id} value={type.id}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="date_issued">Date Issued *</Label>
              <Input
                id="date_issued"
                type="date"
                value={formData.date_issued}
                onChange={(e) => setFormData({...formData, date_issued: e.target.value})}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="owner_department">Owner Department *</Label>
              <Input
                id="owner_department"
                value={formData.owner_department}
                onChange={(e) => setFormData({...formData, owner_department: e.target.value})}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="policy_number">Policy Number</Label>
              <Input
                id="policy_number"
                value={formData.policy_number}
                onChange={(e) => setFormData({...formData, policy_number: e.target.value})}
                placeholder="Auto-generated if empty"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="change_summary">Change Summary</Label>
            <Textarea
              id="change_summary"
              value={formData.change_summary}
              onChange={(e) => setFormData({...formData, change_summary: e.target.value})}
              placeholder="Describe the changes or purpose of this version"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="file">Policy Document *</Label>
            <Input
              id="file"
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => setFile(e.target.files[0])}
              required
            />
          </div>

          {message && (
            <Alert className={message.includes('Error') ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
              <AlertDescription className={message.includes('Error') ? 'text-red-700' : 'text-green-700'}>
                {message}
              </AlertDescription>
            </Alert>
          )}

          <Button type="submit" disabled={uploading} className="w-full">
            {uploading ? 'Uploading...' : 'Upload Policy'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

// Enhanced Category Manager Component
const CategoryManager = ({ categories, onUpdate, showDeleted, onShowDeletedChange, onDelete, onRestore, userRole }) => {
  const [newCategory, setNewCategory] = useState({ name: '', code: '', description: '' });
  const [isAddingCategory, setIsAddingCategory] = useState(false);

  const handleAddCategory = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/categories`, newCategory);
      setNewCategory({ name: '', code: '', description: '' });
      setIsAddingCategory(false);
      onUpdate();
    } catch (error) {
      console.error('Error adding category:', error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Category Management</CardTitle>
            <CardDescription>Manage policy categories and types</CardDescription>
          </div>
          <div className="flex items-center space-x-4">
            {userRole === 'admin' && (
              <div className="flex items-center space-x-2">
                <Label htmlFor="show-deleted-cats">Show Deleted</Label>
                <Switch
                  id="show-deleted-cats"
                  checked={showDeleted}
                  onCheckedChange={onShowDeletedChange}
                />
              </div>
            )}
            {(userRole === 'admin' || userRole === 'policy_manager') && (
              <Dialog open={isAddingCategory} onOpenChange={setIsAddingCategory}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Category
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Category</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleAddCategory} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="cat-name">Name</Label>
                      <Input
                        id="cat-name"
                        value={newCategory.name}
                        onChange={(e) => setNewCategory({...newCategory, name: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cat-code">Code</Label>
                      <Input
                        id="cat-code"
                        value={newCategory.code}
                        onChange={(e) => setNewCategory({...newCategory, code: e.target.value.toUpperCase()})}
                        placeholder="e.g., HR, FIN, OPS"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cat-desc">Description</Label>
                      <Textarea
                        id="cat-desc"
                        value={newCategory.description}
                        onChange={(e) => setNewCategory({...newCategory, description: e.target.value})}
                      />
                    </div>
                    <Button type="submit" className="w-full">Add Category</Button>
                  </form>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map(category => (
            <Card key={category.id} className={`border ${category.is_deleted ? 'opacity-60 bg-red-50' : ''}`}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="outline">{category.code}</Badge>
                  {userRole === 'admin' && (
                    <div className="flex items-center space-x-1">
                      {category.is_deleted ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onRestore(category.id)}
                          className="h-8 px-2 text-green-600"
                          title="Restore category"
                        >
                          <RefreshCw className="h-3 w-3" />
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onDelete(category.id)}
                          className="h-8 px-2 text-red-600"
                          title="Delete category"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  )}
                </div>
                <h3 className="font-medium">{category.name}</h3>
                <p className="text-sm text-slate-600 mt-1">{category.description}</p>
                {category.is_deleted && (
                  <Badge variant="destructive" className="mt-2">Deleted</Badge>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// Enhanced User Manager Component
const UserManager = ({ 
  users, 
  onUpdate, 
  showDeleted, 
  onShowDeletedChange,
  onApprove, 
  onSuspend, 
  onDelete, 
  onRestore, 
  onChangeRole 
}) => {
  const pendingUsers = users.filter(user => !user.is_approved && !user.is_deleted);
  const activeUsers = users.filter(user => user.is_approved || showDeleted);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>User Management</CardTitle>
            <CardDescription>Manage user accounts and permissions</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Label htmlFor="show-deleted-users">Show Deleted</Label>
            <Switch
              id="show-deleted-users"
              checked={showDeleted}
              onCheckedChange={onShowDeletedChange}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {pendingUsers.length > 0 && (
          <div>
            <h3 className="font-medium text-lg mb-4">Pending Approvals</h3>
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Username</TableHead>
                    <TableHead>Full Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pendingUsers.map(user => (
                    <TableRow key={user.id}>
                      <TableCell>{user.username}</TableCell>
                      <TableCell>{user.full_name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          onClick={() => onApprove(user.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Approve
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        <Separator />

        <div>
          <h3 className="font-medium text-lg mb-4">All Users</h3>
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Full Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeUsers.map(user => (
                  <TableRow key={user.id} className={user.is_deleted ? 'opacity-60 bg-red-50' : ''}>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Select
                        value={user.role}
                        onValueChange={(newRole) => onChangeRole(user.id, newRole)}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">User</SelectItem>
                          <SelectItem value="policy_manager">Policy Manager</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col space-y-1">
                        <Badge variant={user.is_active && user.is_approved ? 'default' : 'secondary'}>
                          {user.is_deleted ? 'Deleted' : user.is_suspended ? 'Suspended' : 
                           user.is_active && user.is_approved ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {user.is_deleted ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => onRestore(user.id)}
                            className="h-8 px-2 text-green-600"
                            title="Restore user"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        ) : (
                          <>
                            {user.is_suspended ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => onRestore(user.id)}
                                className="h-8 px-2 text-green-600"
                                title="Restore user"
                              >
                                <UserCheck className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => onSuspend(user.id)}
                                className="h-8 px-2 text-yellow-600"
                                title="Suspend user"
                              >
                                <UserX className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => onDelete(user.id)}
                              className="h-8 px-2 text-red-600"
                              title="Delete user"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto"></div>
          <p className="mt-2 text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
          <Route path="/" element={user ? <Dashboard /> : <Navigate to="/login" />} />
          <Route path="/policy/:policyId" element={user ? <PDFViewer /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

// App with Auth Provider
export default function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}