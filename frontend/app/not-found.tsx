'use client';

import Link from 'next/link';
import { Home, Search, Code } from 'lucide-react';
import { LOGO_URL } from '@/lib/config';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-2xl">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <img 
            src={LOGO_URL} 
            alt="SaladOverflow Logo" 
            className="w-20 h-20 rounded-xl shadow-2xl shadow-sage-600/40"
          />
        </div>

        {/* 404 Message */}
        <h1 className="text-8xl font-bold bg-gradient-to-r from-sage-300 to-sage-500 text-transparent bg-clip-text mb-4">
          404
        </h1>
        <h2 className="text-3xl font-bold text-cream-100 mb-4">
          Page Not Found
        </h2>
        <p className="text-sage-400 mb-8 text-lg">
          Looks like this page got lost in the salad. Let's get you back on track!
        </p>

        {/* Branding */}
        <div className="mb-8">
          <Link href="/" className="inline-block">
            <span className="text-2xl font-bold bg-gradient-to-r from-sage-300 to-sage-500 text-transparent bg-clip-text hover:from-sage-200 hover:to-sage-400 transition">
              SaladOverflow
            </span>
          </Link>
          <p className="text-sm text-sage-400 mt-2">
            Your Developer Q&A Community
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/" className="btn-primary inline-flex items-center justify-center gap-2">
            <Home className="w-5 h-5" />
            Go to Home
          </Link>
          <Link href="/feed" className="btn-secondary inline-flex items-center justify-center gap-2">
            <Search className="w-5 h-5" />
            Browse Feed
          </Link>
        </div>

        {/* Helpful Links */}
        <div className="mt-12 pt-8 border-t-2 border-sage-700/30">
          <p className="text-sage-400 mb-4">Looking for something specific?</p>
          <div className="flex flex-wrap gap-4 justify-center text-sm">
            <Link href="/feed" className="text-sage-300 hover:text-sage-200 transition">
              Feed
            </Link>
            <Link href="/posts/new" className="text-sage-300 hover:text-sage-200 transition">
              Ask Question
            </Link>
            <Link href="/tags" className="text-sage-300 hover:text-sage-200 transition">
              Browse Tags
            </Link>
            <Link href="/bookmarks" className="text-sage-300 hover:text-sage-200 transition">
              Bookmarks
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
