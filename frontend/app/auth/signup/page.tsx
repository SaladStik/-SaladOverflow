'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Code, Mail, Lock, User, Github, Eye, EyeOff } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { LOGO_URL, API_URL } from '@/lib/config';
import toast from 'react-hot-toast';

export default function SignUpPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    display_name: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      await api.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        display_name: formData.display_name || formData.username,
      });

      // Auto-login after registration
      const data = await api.login(formData.username, formData.password);
      // api.login already handles token storage
      setUser(data.user);
      toast.success('Account created successfully!');
      router.push('/feed');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
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
            Create your account
          </h1>
          <p className="mt-2 text-sage-300">
            Join the community of developers
          </p>
        </div>

        {/* Sign Up Form */}
        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-cream-200 mb-2">
                Username *
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cream-300/60" />
                <input
                  id="username"
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="input-primary pl-10"
                  placeholder="johndoe"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-cream-200 mb-2">
                Email *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cream-300/60" />
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-primary pl-10"
                  placeholder="john@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="display_name" className="block text-sm font-medium text-cream-200 mb-2">
                Display Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cream-300/60" />
                <input
                  id="display_name"
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  className="input-primary pl-10"
                  placeholder="John Doe (optional)"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-cream-200 mb-2">
                Password *
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cream-300/60" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input-primary pl-10 pr-10"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-cream-300/60 hover:text-cream-200"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="mt-1 text-xs text-cream-300/60">Must be at least 8 characters</p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-cream-200 mb-2">
                Confirm Password *
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cream-300/60" />
                <input
                  id="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
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
                  Creating account...
                </>
              ) : (
                'Create Account'
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
            Already have an account?{' '}
            <Link href="/auth/signin" className="text-sage-400 hover:text-sage-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-cream-300/60">
          By creating an account, you agree to our{' '}
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
