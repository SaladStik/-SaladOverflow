'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  MapPin, Link2, Twitter, Github, Linkedin, Calendar, 
  Award, MessageSquare, FileText, Edit, Settings, Mail,
  TrendingUp, Clock, CheckCircle, ArrowLeft, Home
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import toast from 'react-hot-toast';

interface UserProfile {
  id: number;
  display_name: string;
  full_name?: string;
  email?: string;
  bio?: string;
  avatar_url?: string;
  banner_url?: string;
  website_url?: string;
  location?: string;
  twitter_handle?: string;
  github_username?: string;
  linkedin_url?: string;
  post_count: number;
  comment_count: number;
  karma_score: number;
  is_verified: boolean;
  created_at: string;
}

interface Post {
  id: number;
  title: string;
  content: string;
  post_type: string;
  created_at: string;
  upvote_count: number;
  downvote_count: number;
  view_count: number;
  answer_count: number;
  tags: Array<{ name: string }>;
}

interface Comment {
  id: number;
  content: string;
  created_at: string;
  upvote_count: number;
  downvote_count: number;
  post_id: number;
  post_title: string;
  is_accepted: boolean;
}

export default function ProfilePage() {
  const params = useParams();
  const router = useRouter();
  const { user: currentUser } = useAuthStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'posts' | 'comments' | 'activity'>('posts');
  const [posts, setPosts] = useState<Post[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);

  const username = params.username as string;
  const isOwnProfile = currentUser?.display_name === username;

  useEffect(() => {
    loadProfile();
  }, [username]);

  useEffect(() => {
    // Load posts when profile is loaded (default tab)
    if (profile && activeTab === 'posts' && posts.length === 0) {
      loadPosts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile]);

  useEffect(() => {
    // Load data when switching tabs
    if (profile) {
      if (activeTab === 'comments' && comments.length === 0) {
        loadComments();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const loadProfile = async () => {
    try {
      const data = await api.getUserProfile(username);
      setProfile(data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        toast.error('User not found');
      } else {
        toast.error('Failed to load profile');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadPosts = async () => {
    setLoadingPosts(true);
    try {
      const data = await api.getPosts({ author: username, page_size: 50 });
      setPosts(data.posts || []);
    } catch (error) {
      console.error('Error loading posts:', error);
      toast.error('Failed to load posts');
    } finally {
      setLoadingPosts(false);
    }
  };

  const loadComments = async () => {
    setLoadingComments(true);
    try {
      const data = await api.getUserComments(username, 50, 0);
      setComments(data || []);
    } catch (error) {
      console.error('Error loading comments:', error);
      toast.error('Failed to load comments');
    } finally {
      setLoadingComments(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-500"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-cream-100 mb-2">User Not Found</h1>
          <p className="text-cream-200 mb-6">The profile you're looking for doesn't exist.</p>
          <Link href="/feed" className="btn-primary">
            Back to Feed
          </Link>
        </div>
      </div>
    );
  }

  const joinDate = new Date(profile.created_at).toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric'
  });

  return (
    <div>
      {/* Banner */}
      <div className="relative h-48 bg-gradient-to-r from-sage-700 via-sage-600 to-sage-800">
        {profile.banner_url && (
          <img 
            src={profile.banner_url} 
            alt="Profile banner" 
            className="w-full h-full object-cover"
          />
        )}
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Profile Header */}
        <div className="relative -mt-20 mb-6">
          <div className="flex flex-col sm:flex-row gap-6 items-start">
            {/* Avatar */}
            <div className="relative">
              <div className="w-32 h-32 rounded-2xl border-4 border-charcoal-400 bg-charcoal-300 overflow-hidden shadow-xl shadow-sage-900/30">
                {profile.avatar_url ? (
                  <img 
                    src={profile.avatar_url} 
                    alt={profile.display_name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-sage-600 to-sage-800">
                    <span className="text-4xl font-bold text-cream-100">
                      {profile.display_name[0].toUpperCase()}
                    </span>
                  </div>
                )}
              </div>
              {profile.is_verified && (
                <div className="absolute -bottom-2 -right-2 w-10 h-10 bg-sage-500 rounded-full flex items-center justify-center border-4 border-charcoal-500 shadow-lg">
                  <CheckCircle className="w-5 h-5 text-cream-100" />
                </div>
              )}
            </div>

            {/* User Info */}
            <div className="flex-1">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h1 className="text-3xl font-bold text-cream-100">
                      {profile.display_name}
                    </h1>
                    {profile.is_verified && (
                      <CheckCircle className="w-6 h-6 text-sage-500" />
                    )}
                  </div>
                  {profile.full_name && (
                    <p className="text-lg text-cream-200 mb-2">{profile.full_name}</p>
                  )}
                  {profile.bio && (
                    <p className="text-cream-200 max-w-2xl">{profile.bio}</p>
                  )}
                </div>

                {isOwnProfile && (
                  <Link href="/settings/profile" className="btn-secondary inline-flex items-center gap-2">
                    <Edit className="w-4 h-4" />
                    Edit Profile
                  </Link>
                )}
              </div>

              {/* Meta Info */}
              <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-cream-200">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>Joined {joinDate}</span>
                </div>
                {profile.location && (
                  <div className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    <span>{profile.location}</span>
                  </div>
                )}
                {profile.email && (
                  <div className="flex items-center gap-1">
                    <Mail className="w-4 h-4" />
                    <span>{profile.email}</span>
                  </div>
                )}
              </div>

              {/* Social Links */}
              <div className="flex flex-wrap gap-3 mt-4">
                {profile.website_url && (
                  <a 
                    href={profile.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cream-200 hover:text-sage-400 transition-colors"
                  >
                    <Link2 className="w-5 h-5" />
                  </a>
                )}
                {profile.twitter_handle && (
                  <a 
                    href={`https://twitter.com/${profile.twitter_handle}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cream-200 hover:text-sage-400 transition-colors"
                  >
                    <Twitter className="w-5 h-5" />
                  </a>
                )}
                {profile.github_username && (
                  <a 
                    href={`https://github.com/${profile.github_username}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cream-200 hover:text-sage-400 transition-colors"
                  >
                    <Github className="w-5 h-5" />
                  </a>
                )}
                {profile.linkedin_url && (
                  <a 
                    href={profile.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cream-200 hover:text-sage-400 transition-colors"
                  >
                    <Linkedin className="w-5 h-5" />
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="card p-4 text-center">
              <div className="flex items-center justify-center gap-2 text-sage-400 mb-1">
                <TrendingUp className="w-5 h-5" />
                <span className="text-2xl font-bold text-cream-100">{profile.karma_score}</span>
              </div>
              <p className="text-sm text-cream-200">Karma</p>
            </div>
            <div className="card p-4 text-center">
              <div className="flex items-center justify-center gap-2 text-sage-400 mb-1">
                <FileText className="w-5 h-5" />
                <span className="text-2xl font-bold text-cream-100">{profile.post_count}</span>
              </div>
              <p className="text-sm text-cream-200">Posts</p>
            </div>
            <div className="card p-4 text-center">
              <div className="flex items-center justify-center gap-2 text-sage-400 mb-1">
                <MessageSquare className="w-5 h-5" />
                <span className="text-2xl font-bold text-cream-100">{profile.comment_count}</span>
              </div>
              <p className="text-sm text-cream-200">Comments</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-charcoal-300 mb-6">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab('posts')}
              className={`pb-3 px-1 border-b-2 font-medium transition-colors ${
                activeTab === 'posts'
                  ? 'border-sage-500 text-sage-400'
                  : 'border-transparent text-cream-200 hover:text-cream-100'
              }`}
            >
              Posts ({profile.post_count})
            </button>
            <button
              onClick={() => setActiveTab('comments')}
              className={`pb-3 px-1 border-b-2 font-medium transition-colors ${
                activeTab === 'comments'
                  ? 'border-sage-500 text-sage-400'
                  : 'border-transparent text-cream-200 hover:text-cream-100'
              }`}
            >
              Comments ({profile.comment_count})
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`pb-3 px-1 border-b-2 font-medium transition-colors ${
                activeTab === 'activity'
                  ? 'border-sage-500 text-sage-400'
                  : 'border-transparent text-cream-200 hover:text-cream-100'
              }`}
            >
              Activity
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="pb-12">
          {activeTab === 'posts' && (
            <div>
              {loadingPosts ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-500"></div>
                </div>
              ) : posts.length > 0 ? (
                <div className="space-y-4">
                  {posts.map((post) => (
                    <Link 
                      key={post.id} 
                      href={`/posts/${post.id}`}
                      className="card p-6 hover:border-sage-600 transition-all block"
                    >
                      <div className="flex gap-4">
                        {/* Vote count */}
                        <div className="flex flex-col items-center gap-1 text-sm">
                          <div className="text-cream-100 font-semibold">
                            {post.upvote_count - post.downvote_count}
                          </div>
                          <div className="text-cream-300 text-xs">votes</div>
                        </div>

                        {/* Answer count */}
                        <div className={`flex flex-col items-center gap-1 text-sm ${
                          post.answer_count > 0 ? 'text-sage-400' : 'text-cream-300'
                        }`}>
                          <div className="font-semibold">{post.answer_count}</div>
                          <div className="text-xs">answers</div>
                        </div>

                        {/* Post info */}
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-cream-100 mb-2 hover:text-sage-400 transition-colors">
                            {post.title}
                          </h3>
                          
                          {/* Tags */}
                          <div className="flex flex-wrap gap-2 mb-3">
                            {post.tags?.map((tag) => (
                              <span 
                                key={tag.name}
                                className="px-2 py-1 text-xs bg-sage-800 text-sage-300 rounded"
                              >
                                {tag.name}
                              </span>
                            ))}
                          </div>

                          {/* Meta */}
                          <div className="flex items-center gap-4 text-sm text-cream-300">
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {new Date(post.created_at).toLocaleDateString()}
                            </span>
                            <span>{post.view_count} views</span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 text-charcoal-200 mx-auto mb-4" />
                  <p className="text-cream-200">No posts yet</p>
                  {isOwnProfile && (
                    <Link href="/posts/new" className="btn-primary mt-4 inline-block">
                      Create Your First Post
                    </Link>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'comments' && (
            <div>
              {loadingComments ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-500"></div>
                </div>
              ) : comments.length > 0 ? (
                <div className="space-y-4">
                  {comments.map((comment) => (
                    <div key={comment.id} className="card p-6">
                      <div className="flex gap-4">
                        {/* Vote count */}
                        <div className="flex flex-col items-center gap-1 text-sm">
                          <div className="text-cream-100 font-semibold">
                            {comment.upvote_count - comment.downvote_count}
                          </div>
                          <div className="text-cream-300 text-xs">votes</div>
                        </div>

                        {/* Accepted badge */}
                        {comment.is_accepted && (
                          <div className="flex flex-col items-center gap-1 text-sm text-sage-400">
                            <CheckCircle className="w-5 h-5 fill-current" />
                            <div className="text-xs">accepted</div>
                          </div>
                        )}

                        {/* Comment info */}
                        <div className="flex-1">
                          <div className="mb-3">
                            <Link 
                              href={`/posts/${comment.post_id}`}
                              className="text-sage-400 hover:text-sage-300 transition-colors font-medium"
                            >
                              {comment.post_title}
                            </Link>
                          </div>

                          {/* Comment content preview */}
                          <div className="text-cream-200 mb-3 line-clamp-3">
                            {comment.content.replace(/<[^>]*>/g, '').substring(0, 200)}
                            {comment.content.replace(/<[^>]*>/g, '').length > 200 && '...'}
                          </div>

                          {/* Meta */}
                          <div className="flex items-center gap-4 text-sm text-cream-300">
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {new Date(comment.created_at).toLocaleDateString()}
                            </span>
                            <Link 
                              href={`/posts/${comment.post_id}#comment-${comment.id}`}
                              className="text-sage-400 hover:text-sage-300 transition-colors"
                            >
                              View in context →
                            </Link>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <MessageSquare className="w-16 h-16 text-charcoal-200 mx-auto mb-4" />
                  <p className="text-cream-200">No comments yet</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'activity' && (
            <div>
              {(loadingPosts || loadingComments) ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-500"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Combine posts and comments, sort by date */}
                  {[
                    ...posts.map(p => ({ type: 'post' as const, data: p, date: new Date(p.created_at) })),
                    ...comments.map(c => ({ type: 'comment' as const, data: c, date: new Date(c.created_at) }))
                  ]
                    .sort((a, b) => b.date.getTime() - a.date.getTime())
                    .slice(0, 20)
                    .map((item, idx) => (
                      <div key={`${item.type}-${item.data.id}`} className="card p-6">
                        <div className="flex items-start gap-4">
                          <div className="text-cream-300">
                            {item.type === 'post' ? (
                              <FileText className="w-5 h-5" />
                            ) : (
                              <MessageSquare className="w-5 h-5" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="text-sm text-cream-300 mb-2">
                              {item.type === 'post' ? 'Posted' : 'Commented on'} · {item.date.toLocaleDateString()}
                            </div>
                            {item.type === 'post' ? (
                              <Link 
                                href={`/posts/${item.data.id}`}
                                className="text-lg font-medium text-cream-100 hover:text-sage-400 transition-colors"
                              >
                                {(item.data as Post).title}
                              </Link>
                            ) : (
                              <div>
                                <Link 
                                  href={`/posts/${(item.data as Comment).post_id}`}
                                  className="text-sage-400 hover:text-sage-300 transition-colors text-sm font-medium mb-2 block"
                                >
                                  {(item.data as Comment).post_title}
                                </Link>
                                <p className="text-cream-200 line-clamp-2">
                                  {item.data.content.replace(/<[^>]*>/g, '').substring(0, 150)}
                                  {item.data.content.replace(/<[^>]*>/g, '').length > 150 && '...'}
                                </p>
                              </div>
                            )}
                          </div>
                          <div className="text-sm text-cream-300">
                            {item.type === 'post' 
                              ? `${item.data.upvote_count - item.data.downvote_count} votes`
                              : (item.data as Comment).is_accepted 
                                ? <CheckCircle className="w-5 h-5 text-sage-400" />
                                : `${item.data.upvote_count - item.data.downvote_count} votes`
                            }
                          </div>
                        </div>
                      </div>
                    ))}
                  {posts.length === 0 && comments.length === 0 && (
                    <div className="text-center py-12">
                      <Clock className="w-16 h-16 text-charcoal-200 mx-auto mb-4" />
                      <p className="text-cream-200">No recent activity</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
