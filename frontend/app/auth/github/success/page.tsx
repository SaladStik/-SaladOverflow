'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';

function GitHubSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setUser } = useAuthStore();

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      toast.error('Authentication failed');
      router.push('/auth/signin');
      return;
    }

    // Store the token
    api.setToken(token);
    
    // Fetch user data
    api.getCurrentUser()
      .then((user) => {
        setUser(user);
        toast.success('Successfully signed in with GitHub!');
        router.push('/feed');
      })
      .catch((error) => {
        console.error('Failed to get user:', error);
        toast.error('Failed to complete authentication');
        router.push('/auth/signin');
      });
  }, [searchParams, router, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-400 mx-auto mb-4"></div>
        <p className="text-sage-300">Completing GitHub sign in...</p>
      </div>
    </div>
  );
}

export default function GitHubSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-400 mx-auto mb-4"></div>
          <p className="text-sage-300">Loading...</p>
        </div>
      </div>
    }>
      <GitHubSuccessContent />
    </Suspense>
  );
}
