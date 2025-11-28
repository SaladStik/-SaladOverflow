import axios, { AxiosError, AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

class ApiClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/${API_VERSION}`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Only redirect to signin if user was actually trying to use an authenticated endpoint
          // Don't redirect for public endpoints like /posts/ (GET)
          const publicEndpoints = [
            '/posts/',
            '/posts/tags/',
            '/users/search',
            '/users/top',
          ];
          
          const url = error.config?.url || '';
          const isPublicEndpoint = publicEndpoints.some(endpoint => url.startsWith(endpoint));
          
          // If it's not a public endpoint, clear token and redirect
          if (!isPublicEndpoint) {
            this.clearToken();
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/signin';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Token management
  setToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  clearToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password });
    if (response.data.access_token) {
      this.setToken(response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }
    return response.data;
  }

  async register(data: {
    email: string;
    username: string;
    display_name: string;
    password: string;
    full_name?: string;
    bio?: string;
  }) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async logout() {
    try {
      await this.client.post('/auth/logout');
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  }

  async checkUsernameAvailability(username: string) {
    const response = await this.client.post('/auth/check-username', null, {
      params: { username }
    });
    return response.data;
  }

  async checkEmailAvailability(email: string) {
    const response = await this.client.get('/auth/check-email', {
      params: { email }
    });
    return response.data;
  }

  async forgotPassword(email: string) {
    const response = await this.client.post('/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(data: { email: string; token: string; new_password: string }) {
    const response = await this.client.post('/auth/reset-password', data);
    return response.data;
  }

  async verifyResetToken(email: string, token: string) {
    const response = await this.client.get('/auth/reset-password/verify', {
      params: { email, token }
    });
    return response.data;
  }

  async verifyEmail(email: string, token: string) {
    const response = await this.client.get('/auth/verify-email', {
      params: { email, token }
    });
    return response.data;
  }

  // Posts endpoints
  async getPosts(params?: {
    page?: number;
    page_size?: number;
    sort?: string;
    post_type?: string;
    tags?: string[];
    author?: string;
    search?: string;
  }) {
    const response = await this.client.get('/posts/', { params });
    return response.data;
  }

  async getPost(postId: number) {
    const response = await this.client.get(`/posts/${postId}`);
    return response.data;
  }

  async createPost(data: {
    title: string;
    content: string;
    post_type: string;
    tags: string[];
  }) {
    const response = await this.client.post('/posts/', data);
    return response.data;
  }

  async updatePost(postId: number, data: {
    title?: string;
    content?: string;
    tags?: string[];
  }) {
    const response = await this.client.put(`/posts/${postId}`, data);
    return response.data;
  }

  async votePost(postId: number, voteType: 'upvote' | 'downvote') {
    const response = await this.client.post(`/posts/${postId}/vote`, { vote_type: voteType });
    return response.data;
  }

  // Comments endpoints
  async getComments(postId: number, sort: string = 'newest') {
    const response = await this.client.get(`/posts/${postId}/comments`, { params: { sort } });
    return response.data;
  }

  async createComment(postId: number, data: {
    content: string;
    parent_id?: number;
    is_answer?: boolean;
  }) {
    const response = await this.client.post(`/posts/${postId}/comments`, data);
    return response.data;
  }

  async voteComment(commentId: number, voteType: 'upvote' | 'downvote') {
    const response = await this.client.post(`/posts/comments/${commentId}/vote`, { vote_type: voteType });
    return response.data;
  }

  async acceptAnswer(postId: number, commentId: number) {
    const response = await this.client.post(`/posts/${postId}/comments/${commentId}/accept`);
    return response.data;
  }

  // Tags endpoints
  async getTags(search?: string, limit: number = 50) {
    const response = await this.client.get('/posts/tags/', { params: { search, limit } });
    return response.data;
  }

  // Users endpoints
  async searchUsers(query: string, limit: number = 20, offset: number = 0) {
    const response = await this.client.get('/users/search', { params: { q: query, limit, offset } });
    return response.data;
  }

  async getTopUsers(sortBy: string = 'karma', limit: number = 10) {
    const response = await this.client.get('/users/top', { params: { sort_by: sortBy, limit } });
    return response.data;
  }

  async getUserProfile(displayName: string) {
    const response = await this.client.get(`/auth/profile/${displayName}`);
    return response.data;
  }

  async getUserComments(displayName: string, limit: number = 50, offset: number = 0) {
    const response = await this.client.get(`/users/${displayName}/comments`, { params: { limit, offset } });
    return response.data;
  }

  async updateProfile(data: any) {
    const response = await this.client.put('/users/profile', data);
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  }

  // Upload endpoints
  async uploadImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/uploads/images', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async uploadProfileImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/uploads/profile-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async uploadBannerImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/uploads/banner-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Bookmark endpoints
  async toggleBookmark(postId: number) {
    const response = await this.client.post(`/posts/${postId}/bookmark`);
    return response.data;
  }

  async getBookmarks(page: number = 1, pageSize: number = 20) {
    const response = await this.client.get('/posts/bookmarks', { params: { page, page_size: pageSize } });
    return response.data;
  }

  // Post management endpoints
  async deletePost(postId: number) {
    const response = await this.client.delete(`/posts/${postId}`);
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
