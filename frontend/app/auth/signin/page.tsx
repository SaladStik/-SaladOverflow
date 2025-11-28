'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Code, Mail, Lock, Github } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { LOGO_URL, API_URL } from '@/lib/config';
import toast from 'react-hot-toast';

export default function SignInPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('Attempting login with:', formData.username);
      const data = await api.login(formData.username, formData.password);
      console.log('Login response:', data);
      // api.login already handles token storage
      setUser(data.user);
      toast.success('Welcome back!');
      router.push('/feed');
    } catch (error: any) {
      console.error('Login error:', error);
      console.error('Error response:', error.response);
      toast.error(error.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-gradient-mesh opacity-30"></div>
      
      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/feed" className="inline-flex items-center gap-2 mb-4">
            <img 
              src={LOGO_URL} 
              alt="SaladOverflow Logo" 
              className="w-12 h-12 rounded-xl"
            />
            <span className="text-2xl font-bold text-gradient">
              SaladOverflow
            </span>
          </Link>
          <h1 className="mt-6 text-3xl font-bold text-cream-100">
            Welcome back
          </h1>
          <p className="mt-2 text-sage-300">
            Sign in to continue to your account
          </p>
        </div>

        {/* Sign In Form */}
        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-cream-200 mb-2">
                Username or Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cream-300/60" />
                <input
                  id="username"
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="input-primary pl-10"
                  placeholder="username or email@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="password" className="block text-sm font-medium text-cream-200">
                  Password
                </label>
                <Link href="/auth/forgot-password" className="text-sm text-sage-400 hover:text-sage-300">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cream-300/60" />
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input-primary pl-10"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-sage-700"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-charcoal-400 text-cream-300/60">Or continue with</span>
              </div>
            </div>

            <a
              href={`${API_URL}/api/v1/auth/github/login`}
              className="mt-4 w-full btn-secondary flex items-center justify-center gap-2"
            >
              <Github className="w-5 h-5" />
              GitHub
            </a>
          </div>

          <p className="mt-6 text-center text-sm text-cream-200">
            Don't have an account?{' '}
            <Link href="/auth/signup" className="text-sage-400 hover:text-sage-300 font-medium">
              Sign up
            </Link>
          </p>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-cream-300/60">
          By signing in, you agree to our{' '}
          <Link href="/terms" className="text-cream-200 hover:text-cream-100">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/privacy" className="text-cream-200 hover:text-cream-100">
            Privacy Policy
          </Link>
        </p>
      </div>
    </div>
  );
}
