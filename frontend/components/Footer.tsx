'use client';

import Link from 'next/link';
import { Code, Heart, Github, Mail } from 'lucide-react';
import { LOGO_URL } from '@/lib/config';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t-2 border-sage-700/40 bg-charcoal-500/50 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-3 group mb-4">
              <img 
                src={LOGO_URL} 
                alt="SaladOverflow Logo" 
                className="w-10 h-10 rounded-lg"
              />
              <span className="text-2xl font-bold bg-gradient-to-r from-sage-300 to-sage-500 text-transparent bg-clip-text">
                SaladOverflow
              </span>
            </Link>
            <p className="text-sage-400 mb-4 max-w-md">
              A self-hosted developer Q&A community where knowledge grows and problems get solved. 
              Built with passion for developers, by developers.
            </p>
            <div className="flex items-center gap-2 text-sm text-sage-400">
              <span>Made with</span>
              <Heart className="w-4 h-4 text-red-500 fill-current" />
              <span>for the dev community</span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-cream-100 mb-4">Community</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/feed" className="text-sage-400 hover:text-sage-300 transition">
                  Feed
                </Link>
              </li>
              <li>
                <Link href="/posts/new" className="text-sage-400 hover:text-sage-300 transition">
                  Ask Question
                </Link>
              </li>
              <li>
                <Link href="/tags" className="text-sage-400 hover:text-sage-300 transition">
                  Browse Tags
                </Link>
              </li>
              <li>
                <Link href="/bookmarks" className="text-sage-400 hover:text-sage-300 transition">
                  Bookmarks
                </Link>
              </li>
            </ul>
          </div>

          {/* About Links */}
          <div>
            <h3 className="font-semibold text-cream-100 mb-4">About</h3>
            <ul className="space-y-2">
              <li>
                <a 
                  href="https://github.com/SaladStik/SaladOverflow" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sage-400 hover:text-sage-300 transition flex items-center gap-2"
                >
                  <Github className="w-4 h-4" />
                  GitHub
                </a>
              </li>
              <li>
                <a 
                  href="mailto:saladoverflow@saladsync.ca" 
                  className="text-sage-400 hover:text-sage-300 transition flex items-center gap-2"
                >
                  <Mail className="w-4 h-4" />
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t-2 border-sage-700/30 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-sm text-sage-400">
            © {currentYear} <span className="text-sage-300 font-semibold">SaladOverflow</span>. 
            All rights reserved.
          </div>
          <div className="flex gap-6 text-sm">
            <Link href="/privacy" className="text-sage-400 hover:text-sage-300 transition">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-sage-400 hover:text-sage-300 transition">
              Terms of Service
            </Link>
            <Link href="/guidelines" className="text-sage-400 hover:text-sage-300 transition">
              Community Guidelines
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
