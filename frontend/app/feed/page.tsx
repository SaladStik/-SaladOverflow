'use client';

import React, { useEffect, useState } from 'react';
import { ArrowUp, ArrowDown, MessageCircle, Bookmark, Share2, Code, Hash, TrendingUp, Award } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { formatTimeAgo, formatNumber, getAvatarUrl } from '@/lib/utils';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function FeedPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookmarked, setBookmarked] = useState<{[key: number]: boolean}>({});
  const [trendingTags, setTrendingTags] = useState<any[]>([]);
  const [topContributors, setTopContributors] = useState<any[]>([]);

  useEffect(() => {
    document.title = 'Feed - SaladOverflow';
  }, []);

  useEffect(() => {
    loadPosts();
    loadTrendingTags();
    loadTopContributors();
  }, []);

  const loadPosts = async () => {
    try {
      const data = await api.getPosts({ page: 1, page_size: 20, sort: 'newest' });
      setPosts(data.posts || []);
      
      // Initialize bookmarked state from API response
      if (data.posts) {
        const bookmarkedState: {[key: number]: boolean} = {};
        data.posts.forEach((post: any) => {
          if (post.is_bookmarked !== undefined) {
            bookmarkedState[post.id] = post.is_bookmarked;
          }
        });
        setBookmarked(bookmarkedState);
      }
    } catch (error) {
      console.error('Failed to load posts:', error);
      toast.error('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  const loadTrendingTags = async () => {
    try {
      const tags = await api.getTags('', 4);
      setTrendingTags(tags);
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  const loadTopContributors = async () => {
    try {
      const users = await api.getTopUsers('karma', 3);
      setTopContributors(users);
    } catch (error) {
      console.error('Failed to load contributors:', error);
    }
  };

  const handleVote = async (postId: number, voteType: 'upvote' | 'downvote') => {
    if (!isAuthenticated) {
      toast.error('Please sign in to vote');
      router.push('/auth/signin');
      return;
    }

    try {
      await api.votePost(postId, voteType);
      await loadPosts(); // Reload to get updated vote counts and user_vote state
      toast.success('Vote recorded');
    } catch (error) {
      console.error('Failed to vote:', error);
      toast.error('Failed to vote');
    }
  };

  const toggleBookmark = async (postId: number) => {
    if (!isAuthenticated) {
      toast.error('Please sign in to bookmark posts');
      router.push('/auth/signin');
      return;
    }
    
    try {
      const wasBookmarked = bookmarked[postId];
      await api.toggleBookmark(postId);
      setBookmarked(prev => ({ ...prev, [postId]: !wasBookmarked }));
      toast.success(wasBookmarked ? 'Bookmark removed' : 'Post bookmarked!');
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
      toast.error('Failed to update bookmark');
    }
  };

  return (
    <div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="hidden lg:block lg:col-span-3 space-y-6">
            {/* Trending Tags */}
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-sage-400" />
                <h2 className="font-semibold text-cream-100">Trending Tags</h2>
              </div>
              <div className="space-y-3">
                {trendingTags.map((tag) => (
                  <Link
                    key={tag.id}
                    href={`/tags/${tag.name}`}
                    className="w-full flex items-center justify-between p-2 hover:bg-sage-600/20 rounded-lg transition group border-2 border-transparent hover:border-sage-600/40"
                  >
                    <span className="text-cream-200 font-medium">#{tag.name}</span>
                    <span className="text-xs text-cream-300/60 group-hover:text-cream-200">
                      {formatNumber(tag.post_count)} posts
                    </span>
                  </Link>
                ))}
              </div>
            </div>

            {/* Top Contributors */}
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Award className="w-5 h-5 text-sage-400" />
                <h2 className="font-semibold text-cream-100">Top Contributors</h2>
              </div>
              <div className="space-y-3">
                {topContributors.map((contributor) => (
                  <Link
                    key={contributor.id}
                    href={`/@${contributor.display_name}`}
                    className="flex items-center gap-3 p-2 hover:bg-sage-600/20 rounded-lg transition cursor-pointer border-2 border-transparent hover:border-sage-600/40"
                  >
                    <img
                      src={contributor.avatar_url || getAvatarUrl(contributor.display_name)}
                      alt={contributor.display_name}
                      className="w-10 h-10 rounded-full ring-2 ring-sage-600/40"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-cream-100 truncate">
                        @{contributor.display_name}
                      </p>
                      <p className="text-xs text-cream-300/60">
                        {formatNumber(contributor.karma_score)} karma
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Main Feed */}
          <div className="lg:col-span-9 space-y-6">
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-400"></div>
              </div>
            ) : posts.length === 0 ? (
              <div className="card p-12 text-center">
                <p className="text-cream-300/80">No posts yet. Be the first to ask a question!</p>
                {isAuthenticated && (
                  <Link href="/posts/new" className="btn-primary inline-block mt-4">
                    Ask Question
                  </Link>
                )}
              </div>
            ) : (
              posts.map((post) => (
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
                      className="flex items-center gap-2 text-cream-300/80 hover:text-sage-400 transition ml-auto"
                    >
                      <Bookmark className={`w-5 h-5 ${bookmarked[post.id] ? 'fill-sage-400 text-sage-400' : ''}`} />
                    </button>
                    <button 
                      onClick={(e) => { 
                        e.stopPropagation();
                        const postUrl = `${window.location.origin}/posts/${post.id}`;
                        if (navigator.share) {
                          navigator.share({
                            title: post.title,
                            url: postUrl
                          }).then(() => {
                            toast.success('Shared successfully');
                          }).catch(() => {
                            // User cancelled or error, fallback to clipboard
                            navigator.clipboard.writeText(postUrl);
                            toast.success('Link copied to clipboard');
                          });
                        } else {
                          navigator.clipboard.writeText(postUrl);
                          toast.success('Link copied to clipboard');
                        }
                      }}
                      className="flex items-center gap-2 text-cream-300/80 hover:text-cream-100 transition"
                    >
                      <Share2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
