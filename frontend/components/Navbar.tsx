'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, Search, PlusCircle, Bookmark, User, LogOut, Settings,
  Menu, X, MessageSquare
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';
import { LOGO_URL } from '@/lib/config';
import SearchModal from './SearchModal';

export default function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    }

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  const handleLogout = () => {
    logout();
    api.clearToken();
    setShowUserMenu(false);
  };

  const isActive = (path: string) => pathname === path;

  // Don't show navbar on auth pages
  if (pathname?.startsWith('/auth/')) {
    return null;
  }

  return (
    <nav className="sticky top-0 z-40 bg-charcoal-400/95 backdrop-blur-md border-b-2 border-sage-600 shadow-xl shadow-charcoal-500/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-8">
            <Link href="/feed" className="flex items-center gap-2 group">
              <img 
                src={LOGO_URL} 
                alt="SaladOverflow Logo" 
                className="w-8 h-8 rounded-lg group-hover:scale-110 transition-transform"
              />
              <span className="text-xl font-bold text-gradient hidden sm:block">
                SaladOverflow
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-1">
              <Link
                href="/feed"
                className={`px-4 py-2 rounded-lg transition flex items-center gap-2 ${
                  pathname === '/feed'
                    ? 'bg-sage-600/40 text-sage-100 shadow-lg shadow-sage-600/30'
                    : 'text-sage-300 hover:text-sage-100 hover:bg-sage-600/30'
                }`}
              >
                <Home className="w-4 h-4" />
                <span className="font-medium">Feed</span>
              </Link>
              <button
                onClick={() => setShowSearchModal(true)}
                className="px-4 py-2 rounded-lg transition flex items-center gap-2 text-sage-300 hover:text-sage-100 hover:bg-sage-600/30"
              >
                <Search className="w-4 h-4" />
                <span className="font-medium">Search</span>
              </button>
            </div>
          </div>

          {/* Right Side - Desktop */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Link
                  href="/posts/new"
                  className="btn-primary inline-flex items-center gap-2"
                >
                  <PlusCircle className="w-4 h-4" />
                  New Post
                </Link>

                <Link
                  href="/bookmarks"
                  className="relative p-2 text-sage-300 hover:text-sage-100 transition"
                >
                  <Bookmark className="w-5 h-5" />
                </Link>

                {/* User Menu */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 p-1 rounded-lg hover:bg-sage-600/30 transition"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sage-500 to-sage-600 flex items-center justify-center overflow-hidden">
                      {user?.avatar_url ? (
                        <img 
                          src={user.avatar_url} 
                          alt={user.display_name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-sm font-bold text-white">
                          {user?.display_name?.[0]?.toUpperCase() || 'U'}
                        </span>
                      )}
                    </div>
                  </button>

                  {/* Dropdown Menu */}
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-56 bg-charcoal-400 border-2 border-sage-600 rounded-lg shadow-2xl shadow-sage-900/40 z-20">
                        <div className="p-3 border-b-2 border-sage-700">
                          <p className="font-medium text-sage-100">{user?.display_name}</p>
                          <p className="text-sm text-sage-300">{user?.email}</p>
                        </div>
                        <div className="py-2">
                          <Link
                            href={`/@${user?.display_name}`}
                            className="flex items-center gap-3 px-4 py-2 text-sage-200 hover:bg-sage-600/30 hover:text-sage-100 transition"
                            onClick={() => setShowUserMenu(false)}
                          >
                            <User className="w-4 h-4" />
                            Profile
                          </Link>
                          <Link
                            href="/settings/profile"
                            className="flex items-center gap-3 px-4 py-2 text-sage-200 hover:bg-sage-600/30 hover:text-sage-100 transition"
                            onClick={() => setShowUserMenu(false)}
                          >
                            <Settings className="w-4 h-4" />
                            Settings
                          </Link>
                        </div>
                        <div className="border-t-2 border-sage-700 py-2">
                          <button
                            onClick={handleLogout}
                            className="flex items-center gap-3 px-4 py-2 text-red-400 hover:bg-red-900/30 transition w-full"
                          >
                            <LogOut className="w-4 h-4" />
                            Log Out
                          </button>
                        </div>
                      </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link href="/auth/signin" className="btn-secondary">
                  Sign In
                </Link>
                <Link href="/auth/signup" className="btn-primary">
                  Sign Up
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="md:hidden p-2 text-sage-300 hover:text-sage-100"
          >
            {showMobileMenu ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {showMobileMenu && (
          <div className="md:hidden border-t-2 border-sage-600 py-4 bg-charcoal-500/90">
            <div className="space-y-2">
              <Link
                href="/feed"
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  pathname === '/feed'
                    ? 'bg-sage-600/40 text-sage-100 shadow-lg shadow-sage-600/30'
                    : 'text-sage-300 hover:bg-sage-600/30 hover:text-sage-100'
                }`}
                onClick={() => setShowMobileMenu(false)}
              >
                <Home className="w-5 h-5" />
                Feed
              </Link>
              <button
                onClick={() => {
                  setShowMobileMenu(false);
                  setShowSearchModal(true);
                }}
                className="flex items-center gap-3 px-4 py-3 rounded-lg transition text-sage-300 hover:bg-sage-600/30 hover:text-sage-100 w-full text-left"
              >
                <Search className="w-5 h-5" />
                Search
              </button>

              {isAuthenticated ? (
                <>
                  <Link
                    href="/posts/new"
                    className="flex items-center gap-3 px-4 py-3 text-sage-300 hover:bg-sage-600/30 hover:text-sage-100 rounded-lg transition"
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <PlusCircle className="w-5 h-5" />
                    New Post
                  </Link>
                  <Link
                    href={`/@${user?.display_name}`}
                    className="flex items-center gap-3 px-4 py-3 text-sage-300 hover:bg-sage-600/30 hover:text-sage-100 rounded-lg transition"
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <User className="w-5 h-5" />
                    Profile
                  </Link>
                  <Link
                    href="/settings/profile"
                    className="flex items-center gap-3 px-4 py-3 text-sage-300 hover:bg-sage-600/30 hover:text-sage-100 rounded-lg transition"
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <Settings className="w-5 h-5" />
                    Settings
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout();
                      setShowMobileMenu(false);
                    }}
                    className="flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-900/30 rounded-lg transition w-full"
                  >
                    <LogOut className="w-5 h-5" />
                    Log Out
                  </button>
                </>
              ) : (
                <div className="px-4 space-y-2">
                  <Link
                    href="/auth/signin"
                    className="btn-secondary w-full justify-center"
                    onClick={() => setShowMobileMenu(false)}
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/auth/signup"
                    className="btn-primary w-full justify-center"
                    onClick={() => setShowMobileMenu(false)}
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Search Modal */}
      <SearchModal 
        isOpen={showSearchModal} 
        onClose={() => setShowSearchModal(false)} 
      />
    </nav>
  );
}
