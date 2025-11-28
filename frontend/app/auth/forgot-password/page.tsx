'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Code, Mail, ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.forgotPassword(email);
      setSubmitted(true);
      toast.success('Password reset email sent!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-gradient-mesh opacity-30"></div>
        
        <div className="relative w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center gap-2">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Code className="w-7 h-7 text-white" />
              </div>
              <span className="text-2xl font-bold text-gradient">
                SaladOverflow
              </span>
            </Link>
          </div>

          {/* Success Message */}
          <div className="card p-8 text-center">
            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="w-8 h-8 text-green-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-100 mb-2">Check your email</h2>
            <p className="text-slate-400 mb-6">
              If an account exists with <span className="text-slate-300 font-medium">{email}</span>, 
              you will receive a password reset link shortly.
            </p>
            <p className="text-sm text-slate-500 mb-6">
              Didn't receive the email? Check your spam folder or try again.
            </p>
            <Link href="/auth/signin" className="btn-primary inline-flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-gradient-mesh opacity-30"></div>
      
      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Code className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-gradient">
              SaladOverflow
            </span>
          </Link>
          <h1 className="mt-6 text-3xl font-bold text-slate-100">
            Forgot your password?
          </h1>
          <p className="mt-2 text-slate-400">
            No worries, we'll send you reset instructions
          </p>
        </div>

        {/* Forgot Password Form */}
        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-primary pl-10"
                  placeholder="your@email.com"
                  required
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Enter the email address associated with your account
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Sending...
                </>
              ) : (
                'Send Reset Link'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link href="/auth/signin" className="text-sm text-slate-400 hover:text-slate-300 inline-flex items-center gap-1">
              <ArrowLeft className="w-4 h-4" />
              Back to Sign In
            </Link>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-slate-500">
          Remember your password?{' '}
          <Link href="/auth/signin" className="text-slate-400 hover:text-slate-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
