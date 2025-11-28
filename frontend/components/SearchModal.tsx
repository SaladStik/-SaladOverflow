'use client';

import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Search, X, Hash, User, FileText, TrendingUp, Clock } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { formatTimeAgo } from '@/lib/utils';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any>({
    posts: [],
    users: [],
    tags: [],
  });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'posts' | 'users' | 'tags'>('all');
  const inputRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  // Helper function to strip HTML tags and decode entities
  const stripHtml = (html: string): string => {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
      setQuery('');
      setSearchResults({ posts: [], users: [], tags: [] });
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (query.trim().length > 0) {
      const debounce = setTimeout(() => {
        performSearch();
      }, 300);

      return () => clearTimeout(debounce);
    } else {
      setSearchResults({ posts: [], users: [], tags: [] });
    }
  }, [query]);

  const performSearch = async () => {
    setLoading(true);
    try {
      const [posts, users, tags] = await Promise.all([
        api.getPosts({ page: 1, page_size: 5, search: query }).catch(() => ({ posts: [] })),
        api.searchUsers(query, 5).catch(() => []),
        api.getTags(query, 5).catch(() => []),
      ]);

      setSearchResults({
        posts: posts.posts || [],
        users: users || [],
        tags: tags || [],
      });
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const hasResults = searchResults.posts.length > 0 || searchResults.users.length > 0 || searchResults.tags.length > 0;
  const showPosts = activeTab === 'all' || activeTab === 'posts';
  const showUsers = activeTab === 'all' || activeTab === 'users';
  const showTags = activeTab === 'all' || activeTab === 'tags';

  const modalContent = (
    <div className="fixed inset-0 z-[100]">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/90 backdrop-blur-sm"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div 
        ref={modalRef}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 w-full max-w-3xl mx-4 bg-charcoal-300 border-2 border-sage-600 rounded-2xl shadow-2xl shadow-sage-900/60 overflow-hidden z-10"
        style={{ transform: 'translate(-50%, calc(-50% - 20px))' }}
      >
        {/* Search Input */}
        <div className="relative border-b-2 border-sage-700">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-sage-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for posts, users, or tags..."
            className="w-full pl-16 pr-16 py-5 bg-transparent text-lg text-cream-100 placeholder-cream-300/40 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="absolute right-6 top-1/2 -translate-y-1/2 p-2 text-cream-300/80 hover:text-cream-100 rounded-lg hover:bg-sage-600/30 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        {query.trim().length > 0 && (
          <div className="flex items-center gap-2 px-6 py-3 border-b-2 border-sage-700 bg-charcoal-400/50">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'all'
                  ? 'bg-sage-500 text-cream-100 shadow-lg shadow-sage-500/40'
                  : 'text-cream-200 hover:text-cream-100 hover:bg-sage-600/30'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setActiveTab('posts')}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'posts'
                  ? 'bg-sage-500 text-cream-100 shadow-lg shadow-sage-500/40'
                  : 'text-cream-200 hover:text-cream-100 hover:bg-sage-600/30'
              }`}
            >
              Posts ({searchResults.posts.length})
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'users'
                  ? 'bg-sage-500 text-cream-100 shadow-lg shadow-sage-500/40'
                  : 'text-cream-200 hover:text-cream-100 hover:bg-sage-600/30'
              }`}
            >
              Users ({searchResults.users.length})
            </button>
            <button
              onClick={() => setActiveTab('tags')}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'tags'
                  ? 'bg-sage-500 text-cream-100 shadow-lg shadow-sage-500/40'
                  : 'text-cream-200 hover:text-cream-100 hover:bg-sage-600/30'
              }`}
            >
              Tags ({searchResults.tags.length})
            </button>
          </div>
        )}

        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto">
          {query.trim().length === 0 ? (
            <div className="p-12 text-center">
              <Search className="w-16 h-16 text-sage-700 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-cream-200 mb-2">Start searching</h3>
              <p className="text-sm text-cream-300/60">
                Search for posts, users, or tags across SaladOverflow
              </p>
            </div>
          ) : loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-400 mx-auto"></div>
              <p className="text-cream-200 mt-4">Searching...</p>
            </div>
          ) : !hasResults ? (
            <div className="p-12 text-center">
              <FileText className="w-16 h-16 text-sage-700 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-cream-200 mb-2">No results found</h3>
              <p className="text-sm text-cream-300/60">
                Try adjusting your search terms or browse trending topics
              </p>
            </div>
          ) : (
            <div className="divide-y-2 divide-sage-700">
              {/* Posts */}
              {showPosts && searchResults.posts.length > 0 && (
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-cream-300/80 uppercase tracking-wide mb-3 px-2">
                    Posts
                  </h3>
                  <div className="space-y-2">
                    {searchResults.posts.map((post: any) => (
                      <Link
                        key={post.id}
                        href={`/posts/${post.id}`}
                        onClick={onClose}
                        className="block p-3 rounded-lg hover:bg-charcoal-200/80 border-2 border-transparent hover:border-sage-600 transition group"
                      >
                        <div className="flex items-start gap-3">
                          <FileText className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <h4 className="text-cream-100 font-medium group-hover:text-cream-50 transition line-clamp-1">
                              {post.title}
                            </h4>
                            {post.content && (
                              <p className="text-sm text-cream-300/60 line-clamp-2 mt-1">
                                {stripHtml(post.content).substring(0, 150)}...
                              </p>
                            )}
                            <div className="flex items-center gap-3 mt-2 text-xs text-cream-300/50">
                              <span>{post.author_display_name || 'Unknown'}</span>
                              <span>•</span>
                              <span>{formatTimeAgo(post.created_at)}</span>
                              <span>•</span>
                              <span>{((post.upvote_count || 0) - (post.downvote_count || 0))} votes</span>
                            </div>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Users */}
              {showUsers && searchResults.users.length > 0 && (
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-cream-300/80 uppercase tracking-wide mb-3 px-2">
                    Users
                  </h3>
                  <div className="space-y-2">
                    {searchResults.users.map((user: any) => (
                      <Link
                        key={user.id}
                        href={`/@${user.display_name}`}
                        onClick={onClose}
                        className="block p-3 rounded-lg hover:bg-charcoal-200/80 border-2 border-transparent hover:border-sage-600 transition group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-sage-500 to-sage-700 flex items-center justify-center flex-shrink-0 overflow-hidden shadow-lg shadow-sage-600/40">
                            {user.avatar_url ? (
                              <img src={user.avatar_url} alt={user.display_name} className="w-full h-full object-cover" />
                            ) : (
                              <span className="text-sm font-bold text-cream-100">
                                {user.display_name[0].toUpperCase()}
                              </span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-cream-100 font-medium group-hover:text-cream-50 transition">
                              {user.display_name}
                            </h4>
                            {user.bio && (
                              <p className="text-sm text-cream-300/60 line-clamp-1">{user.bio}</p>
                            )}
                            <div className="flex items-center gap-3 mt-1 text-xs text-cream-300/50">
                              <span>{user.karma_score || 0} karma</span>
                              <span>•</span>
                              <span>{user.post_count || 0} posts</span>
                            </div>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Tags */}
              {showTags && searchResults.tags.length > 0 && (
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-cream-300/80 uppercase tracking-wide mb-3 px-2">
                    Tags
                  </h3>
                  <div className="space-y-2">
                    {searchResults.tags.map((tag: any) => (
                      <Link
                        key={tag.id}
                        href={`/tags/${tag.name}`}
                        onClick={onClose}
                        className="block p-3 rounded-lg hover:bg-charcoal-200/80 border-2 border-transparent hover:border-sage-600 transition group"
                      >
                        <div className="flex items-center gap-3">
                          <Hash className="w-5 h-5 text-sage-400 flex-shrink-0" />
                          <div className="flex-1">
                            <h4 className="text-cream-100 font-medium group-hover:text-cream-50 transition">
                              {tag.name}
                            </h4>
                            {tag.description && (
                              <p className="text-sm text-cream-300/60 line-clamp-1">{tag.description}</p>
                            )}
                            <p className="text-xs text-cream-300/50 mt-1">
                              {tag.post_count || 0} posts
                            </p>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="border-t-2 border-sage-700 px-6 py-3 bg-charcoal-400/50">
          <p className="text-xs text-cream-300/60 text-center">
            Press <kbd className="px-2 py-1 bg-charcoal-500 border-2 border-sage-600 rounded text-cream-200">ESC</kbd> to close
          </p>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
