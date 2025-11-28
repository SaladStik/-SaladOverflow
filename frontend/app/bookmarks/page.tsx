'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Bookmark, ArrowLeft, Loader2, ArrowUp, ArrowDown, MessageCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { formatTimeAgo } from '@/lib/utils';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';

interface Post {
  id: number;
  title: string;
  content: string;
  content_plain?: string;
  post_type: 'question' | 'discussion' | 'announcement';
  author_display_name: string;
  author_avatar?: string;
  author_is_verified: boolean;
  tags: Array<{ id: number; name: string }>;
  upvote_count: number;
  downvote_count: number;
  comment_count: number;
  view_count: number;
  created_at: string;
  created_at_relative?: string;
  is_answered?: boolean;
  user_vote?: 'upvote' | 'downvote' | null;
}

interface BookmarksResponse {
  posts: Post[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function BookmarksPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [bookmarks, setBookmarks] = useState<BookmarksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [removedBookmarks, setRemovedBookmarks] = useState<Set<number>>(new Set());

  useEffect(() => {
    document.title = 'Bookmarks - SaladOverflow';
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/signin');
      return;
    }
    loadBookmarks();
  }, [isAuthenticated, page]);

  const loadBookmarks = async () => {
    try {
      setLoading(true);
      const data = await api.getBookmarks(page, 20);
      setBookmarks(data);
    } catch (error: any) {
      console.error('Error loading bookmarks:', error);
      toast.error('Failed to load bookmarks');
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (postId: number, voteType: 'upvote' | 'downvote') => {
    if (!isAuthenticated) {
      toast.error('Please sign in to vote');
      return;
    }

    try {
      await api.votePost(postId, voteType);
      await loadBookmarks();
      toast.success('Vote recorded');
    } catch (error) {
      console.error('Error voting:', error);
      toast.error('Failed to vote');
    }
  };

  const toggleBookmark = async (postId: number) => {
    if (!isAuthenticated) {
      toast.error('Please sign in to bookmark posts');
      return;
    }

    try {
      await api.toggleBookmark(postId);
      // Add to removed set for instant UI update
      setRemovedBookmarks(prev => new Set(prev).add(postId));
      toast.success('Bookmark removed');
      // Reload bookmarks after a short delay
      setTimeout(() => loadBookmarks(), 300);
    } catch (error) {
      console.error('Error removing bookmark:', error);
      toast.error('Failed to remove bookmark');
    }
  };

  const getAvatarUrl = (displayName: string) => {
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(displayName)}`;
  };

  if (loading && !bookmarks) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-12 h-12 animate-spin text-sage-400" />
      </div>
    );
  }

  const visiblePosts = bookmarks?.posts.filter(post => !removedBookmarks.has(post.id)) || [];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/feed"
          className="inline-flex items-center gap-2 text-sage-400 hover:text-sage-300 mb-4 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Feed
        </Link>
        
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-sage-600/30 rounded-lg">
            <Bookmark className="w-6 h-6 text-sage-300" />
          </div>
          <h1 className="text-3xl font-bold text-sage-100">My Bookmarks</h1>
        </div>
        <p className="text-sage-400">
          {bookmarks?.total_count || 0} saved {bookmarks?.total_count === 1 ? 'post' : 'posts'}
        </p>
      </div>

      {/* Bookmarked Posts */}
      {visiblePosts.length > 0 ? (
        <div className="space-y-4">
          {visiblePosts.map((post) => (
            <div key={post.id} className="card-hover overflow-hidden">
              {/* Post Header */}
              <Link href={`/posts/${post.id}`} className="block p-6 pb-4">
                <div className="flex items-center gap-3 mb-4">
                  <img
                    src={post.author_avatar || getAvatarUrl(post.author_display_name)}
                    alt={post.author_display_name}
                    className="w-11 h-11 rounded-full ring-2 ring-sage-600/40"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-cream-100 hover:text-cream-50 transition">
                        @{post.author_display_name}
                      </span>
                      {post.is_answered && (
                        <span className="px-2 py-0.5 bg-sage-500/30 text-cream-200 text-xs font-medium rounded-full border border-sage-500/40">
                          Solved
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-cream-300/60">{post.created_at_relative || formatTimeAgo(post.created_at)}</p>
                  </div>
                </div>

                <h2 className="text-xl font-semibold text-cream-100 mb-2 hover:text-cream-50 transition">
                  {post.title}
                </h2>
                
                <div className="text-cream-200 mb-4 line-clamp-3 markdown">
                  <ReactMarkdown>{post.content_plain?.substring(0, 200) + '...'}</ReactMarkdown>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {post.tags.map((tag: any) => (
                    <span
                      key={tag.id}
                      className="px-3 py-1 bg-sage-600/20 text-cream-200 text-sm font-medium rounded-full border-2 border-sage-600/40"
                    >
                      #{tag.name}
                    </span>
                  ))}
                </div>
              </Link>

              {/* Post Actions */}
              <div className="flex items-center gap-6 px-6 py-4 border-t-2 border-sage-700/40">
                {/* Voting */}
                <div className="flex items-center gap-3">
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleVote(post.id, 'upvote'); }}
                    className={`p-1 rounded transition ${
                      post.user_vote === 'upvote'
                        ? 'text-sage-400 bg-sage-500/20'
                        : 'text-cream-300/60 hover:text-sage-400 hover:bg-sage-500/10'
                    }`}
                  >
                    <ArrowUp className="w-5 h-5" />
                  </button>
                  <span className="text-sm font-bold text-cream-100 min-w-[2ch] text-center">
                    {(post.upvote_count || 0) - (post.downvote_count || 0)}
                  </span>
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleVote(post.id, 'downvote'); }}
                    className={`p-1 rounded transition ${
                      post.user_vote === 'downvote'
                        ? 'text-red-400 bg-red-500/20'
                        : 'text-cream-300/60 hover:text-red-400 hover:bg-red-500/10'
                    }`}
                  >
                    <ArrowDown className="w-5 h-5" />
                  </button>
                </div>
                <Link href={`/posts/${post.id}`} className="flex items-center gap-2 text-cream-300/80 hover:text-cream-100 transition">
                  <MessageCircle className="w-5 h-5" />
                  <span className="font-medium">{post.comment_count}</span>
                </Link>
                <button 
                  onClick={(e) => { e.stopPropagation(); toggleBookmark(post.id); }}
                  className="flex items-center gap-2 text-sage-400 hover:text-sage-300 transition ml-auto fill-sage-400"
                >
                  <Bookmark className="w-5 h-5 fill-sage-400" />
                </button>
              </div>
            </div>
          ))}

          {/* Pagination */}
          {bookmarks && bookmarks.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-charcoal-300 text-sage-200 rounded-lg hover:bg-charcoal-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                Previous
              </button>
              <span className="text-sage-300">
                Page {page} of {bookmarks.total_pages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(bookmarks.total_pages, p + 1))}
                disabled={page === bookmarks.total_pages}
                className="px-4 py-2 bg-charcoal-300 text-sage-200 rounded-lg hover:bg-charcoal-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                Next
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <Bookmark className="w-16 h-16 text-sage-700 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-sage-200 mb-2">No Bookmarks Yet</h2>
          <p className="text-sage-400 mb-6">
            Start bookmarking posts to save them for later
          </p>
          <Link href="/feed" className="btn-primary inline-block">
            Browse Posts
          </Link>
        </div>
      )}
    </div>
  );
}
