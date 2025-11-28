'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Mail, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [verifying, setVerifying] = useState(true);
  const [verificationSuccess, setVerificationSuccess] = useState(false);
  const [verificationError, setVerificationError] = useState('');
  const [email, setEmail] = useState('');

  useEffect(() => {
    const emailParam = searchParams.get('email');
    const tokenParam = searchParams.get('token');

    if (!emailParam || !tokenParam) {
      setVerificationError('Invalid verification link');
      setVerifying(false);
      return;
    }

    setEmail(emailParam);

    // Verify the email
    api.verifyEmail(emailParam, tokenParam)
      .then((response) => {
        if (response.message || response.verified_at) {
          setVerificationSuccess(true);
          toast.success('Email verified successfully!');
          // Redirect to signin after 3 seconds
          setTimeout(() => {
            router.push('/auth/signin');
          }, 3000);
        } else {
          setVerificationError('Verification failed');
        }
      })
      .catch((error: any) => {
        const errorDetail = error.response?.data?.detail || 'Invalid or expired verification link';
        
        // Check if the error is about an already verified email
        // In this case, we should show a success message instead
        if (errorDetail.toLowerCase().includes('expired') || 
            errorDetail.toLowerCase().includes('invalid') ||
            errorDetail.toLowerCase().includes('used')) {
          // The token might have been used - show a helpful message
          setVerificationError('This verification link has already been used. If your email is verified, you can sign in now.');
        } else {
          setVerificationError(errorDetail);
        }
        toast.error(errorDetail);
      })
      .finally(() => {
        setVerifying(false);
      });
  }, [searchParams, router]);

  if (verifying) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 bg-charcoal-950">
        <div className="absolute inset-0 bg-gradient-to-br from-sage-900/10 via-transparent to-sage-800/10"></div>
        
        <div className="relative text-center">
          <div className="w-20 h-20 bg-sage-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-10 h-10 text-sage-400 animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-cream-100 mb-2">Verifying your email</h2>
          <p className="text-cream-300">Please wait while we verify your email address...</p>
        </div>
      </div>
    );
  }

  if (verificationSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 bg-charcoal-950">
        <div className="absolute inset-0 bg-gradient-to-br from-sage-900/10 via-transparent to-sage-800/10"></div>
        
        <div className="relative w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center gap-3">
              <div className="w-12 h-12 bg-sage-600 rounded-xl flex items-center justify-center">
                <svg className="w-7 h-7 text-charcoal-950" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                </svg>
              </div>
              <span className="text-2xl font-bold text-cream-100">
                SaladOverflow
              </span>
            </Link>
          </div>

          {/* Success Message */}
          <div className="bg-charcoal-900 border border-sage-800/30 rounded-xl p-8 text-center shadow-xl">
            <div className="w-20 h-20 bg-sage-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-sage-400" />
            </div>
            <h2 className="text-2xl font-bold text-cream-100 mb-3">Email Verified!</h2>
            <p className="text-cream-300 mb-6">
              Your email address has been verified successfully. You can now sign in to your account.
            </p>
            {email && (
              <div className="bg-charcoal-800 border border-sage-800/20 rounded-lg p-4 mb-6">
                <p className="text-sm text-cream-400">Verified email:</p>
                <p className="text-cream-100 font-medium">{email}</p>
              </div>
            )}
            <p className="text-sm text-cream-400 mb-6">
              Redirecting to sign in page...
            </p>
            <Link 
              href="/auth/signin" 
              className="inline-block w-full bg-sage-600 hover:bg-sage-700 text-charcoal-950 font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Sign In Now
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 bg-charcoal-950">
      <div className="absolute inset-0 bg-gradient-to-br from-red-900/10 via-transparent to-red-800/10"></div>
      
      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-3">
            <div className="w-12 h-12 bg-sage-600 rounded-xl flex items-center justify-center">
              <svg className="w-7 h-7 text-charcoal-950" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
              </svg>
            </div>
            <span className="text-2xl font-bold text-cream-100">
              SaladOverflow
            </span>
          </Link>
        </div>

        {/* Error Message */}
        <div className="bg-charcoal-900 border border-red-800/30 rounded-xl p-8 text-center shadow-xl">
          <div className="w-20 h-20 bg-red-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <XCircle className="w-10 h-10 text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-cream-100 mb-3">Verification Failed</h2>
          <p className="text-cream-300 mb-6">
            {verificationError || 'We could not verify your email address. The link may have expired or is invalid.'}
          </p>
          
          <div className="space-y-3">
            <Link 
              href="/auth/signin" 
              className="inline-block w-full bg-sage-600 hover:bg-sage-700 text-charcoal-950 font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Go to Sign In
            </Link>
            <p className="text-sm text-cream-400">
              Need help?{' '}
              <Link href="/" className="text-sage-400 hover:text-sage-300">
                Contact support
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-charcoal-950">
        <div className="w-20 h-20 bg-sage-600/20 rounded-full flex items-center justify-center">
          <Loader2 className="w-10 h-10 text-sage-400 animate-spin" />
        </div>
      </div>
    }>
      <VerifyEmailForm />
    </Suspense>
  );
}
