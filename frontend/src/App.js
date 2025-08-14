import React, { useState, useEffect, useContext, createContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
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
  User
} from 'lucide-react';
import './App.css';

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

          {isLogin && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800 font-medium">Default Admin Credentials:</p>
              <p className="text-sm text-blue-700">Username: admin</p>
              <p className="text-sm text-blue-700">Password: admin123</p>
            </div>
          )}
        </CardContent>
      </Card>
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

// Dashboard Component
const Dashboard = () => {
  const { user } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');

  useEffect(() => {
    fetchPolicies();
    fetchCategories();
    if (user.role === 'admin') {
      fetchUsers();
    }
  }, [user]);

  const fetchPolicies = async () => {
    try {
      const response = await axios.get(`${API}/policies`);
      setPolicies(response.data);
    } catch (error) {
      console.error('Error fetching policies:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
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

  const handleApproveUser = async (userId) => {
    try {
      await axios.patch(`${API}/users/${userId}/approve`);
      fetchUsers();
    } catch (error) {
      console.error('Error approving user:', error);
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

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        <Tabs defaultValue="policies" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="policies" className="flex items-center space-x-2">
              <FileText className="h-4 w-4" />
              <span>Policies</span>
            </TabsTrigger>
            <TabsTrigger value="categories" className="flex items-center space-x-2">
              <FolderOpen className="h-4 w-4" />
              <span>Categories</span>
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
                <CardTitle>Policy Management</CardTitle>
                <CardDescription>
                  Browse, search, and manage organizational policies
                </CardDescription>
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
                        {categories.map(category => (
                          <SelectItem key={category.id} value={category.id}>
                            {category.name}
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
                            {policy.policy_type.replace('_', ' ')}
                          </TableCell>
                          <TableCell>v{policy.version}</TableCell>
                          <TableCell>
                            <Badge 
                              variant={policy.status === 'active' ? 'default' : 'outline'}
                              className={policy.status === 'active' ? 'bg-green-600' : ''}
                            >
                              {policy.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => window.open(`${BACKEND_URL}${policy.file_url}`, '_blank')}
                                className="h-8 px-2"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDownload(policy.id)}
                                className="h-8 px-2"
                              >
                                <Download className="h-4 w-4" />
                              </Button>
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
            <CategoryManager categories={categories} onUpdate={fetchCategories} />
          </TabsContent>

          {user.role === 'admin' && (
            <TabsContent value="users">
              <UserManager users={users} onUpdate={fetchUsers} onApprove={handleApproveUser} />
            </TabsContent>
          )}

          {(user.role === 'admin' || user.role === 'policy_manager') && (
            <TabsContent value="upload">
              <PolicyUploader categories={categories} onUpload={fetchPolicies} />
            </TabsContent>
          )}
        </Tabs>
      </main>
    </div>
  );
};

// Policy Uploader Component
const PolicyUploader = ({ categories, onUpload }) => {
  const [formData, setFormData] = useState({
    title: '',
    category_id: '',
    policy_type: 'policy',
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
        policy_type: 'policy',
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
              <Select value={formData.policy_type} onValueChange={(value) => setFormData({...formData, policy_type: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="policy">Policy</SelectItem>
                  <SelectItem value="procedure">Procedure</SelectItem>
                  <SelectItem value="guideline">Guideline</SelectItem>
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

// Category Manager Component
const CategoryManager = ({ categories, onUpdate }) => {
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
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map(category => (
            <Card key={category.id} className="border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="outline">{category.code}</Badge>
                </div>
                <h3 className="font-medium">{category.name}</h3>
                <p className="text-sm text-slate-600 mt-1">{category.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// User Manager Component
const UserManager = ({ users, onUpdate, onApprove }) => {
  const pendingUsers = users.filter(user => !user.is_approved);
  const activeUsers = users.filter(user => user.is_approved);

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Management</CardTitle>
        <CardDescription>Manage user accounts and permissions</CardDescription>
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
          <h3 className="font-medium text-lg mb-4">Active Users</h3>
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Full Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeUsers.map(user => (
                  <TableRow key={user.id}>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {user.role.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? 'default' : 'secondary'}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
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