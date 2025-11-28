'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser } = useAuthStore();

  useEffect(() => {
    // Check if user has a token on mount
    const token = api.getToken();
    if (token) {
      // Fetch current user data
      api.getCurrentUser()
        .then((user) => {
          setUser(user);
        })
        .catch((error) => {
          // Token is invalid, clear it
          api.clearToken();
          setUser(null);
        });
    }
  }, [setUser]);

  return <>{children}</>;
}
