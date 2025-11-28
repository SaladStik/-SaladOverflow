'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Hash, TrendingUp, Clock } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { formatTimeAgo } from '@/lib/utils';

export default function TagPage() {
  const params = useParams();
  const tagName = params.name as string;
  const [posts, setPosts] = useState<any[]>([]);
  const [tag, setTag] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'newest' | 'popular' | 'active'>('newest');

  useEffect(() => {
    loadTagAndPosts();
  }, [tagName, sortBy]);

  const loadTagAndPosts = async () => {
    try {
      setLoading(true);
      
      // Load tag info
      const tags = await api.getTags(tagName, 1);
      const foundTag = tags.find((t: any) => t.name.toLowerCase() === tagName.toLowerCase());
      setTag(foundTag);

      // Load posts with this tag - try without filtering first, then filter client-side
      // This avoids the 422 error from the backend
      const sortParam = sortBy === 'newest' ? 'newest' : sortBy === 'popular' ? 'most_voted' : 'active';
      const response = await api.getPosts({ 
        page: 1, 
        page_size: 50,
        sort: sortParam
      });
      
      // Filter posts by tag on the client side
      const filteredPosts = (response.posts || []).filter((post: any) => 
        post.tags && post.tags.some((t: any) => t.name.toLowerCase() === tagName.toLowerCase())
      );
      
      setPosts(filteredPosts);
    } catch (error) {
      console.error('Error loading tag:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-400"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tag Header */}
        <div className="card p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-sage-600/20 border-2 border-sage-600/40 rounded-xl">
              <Hash className="w-8 h-8 text-sage-400" />
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-cream-100 mb-2">
                {tagName}
              </h1>
              {tag?.description && (
                <p className="text-cream-200 mb-4">{tag.description}</p>
              )}
              <div className="flex items-center gap-4 text-sm text-cream-300">
                <span>{tag?.post_count || posts.length} posts</span>
                {tag?.created_at && (
                  <>
                    <span>•</span>
                    <span>Created {formatTimeAgo(tag.created_at)}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Sort Options */}
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => setSortBy('newest')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              sortBy === 'newest'
                ? 'bg-sage-600 text-cream-100 border-2 border-sage-500 shadow-lg shadow-sage-600/40'
                : 'bg-charcoal-300 text-cream-200 border-2 border-sage-700 hover:text-cream-100 hover:bg-sage-600/20'
            }`}
          >
            <Clock className="w-4 h-4 inline mr-2" />
            Newest
          </button>
          <button
            onClick={() => setSortBy('popular')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              sortBy === 'popular'
                ? 'bg-sage-600 text-cream-100 border-2 border-sage-500 shadow-lg shadow-sage-600/40'
                : 'bg-charcoal-300 text-cream-200 border-2 border-sage-700 hover:text-cream-100 hover:bg-sage-600/20'
            }`}
          >
            <TrendingUp className="w-4 h-4 inline mr-2" />
            Popular
          </button>
          <button
            onClick={() => setSortBy('active')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              sortBy === 'active'
                ? 'bg-sage-600 text-cream-100 border-2 border-sage-500 shadow-lg shadow-sage-600/40'
                : 'bg-charcoal-300 text-cream-200 border-2 border-sage-700 hover:text-cream-100 hover:bg-sage-600/20'
            }`}
          >
            <TrendingUp className="w-4 h-4 inline mr-2" />
            Active
          </button>
        </div>

        {/* Posts List */}
        {posts.length === 0 ? (
          <div className="card p-12 text-center">
            <Hash className="w-16 h-16 text-charcoal-200 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-cream-100 mb-2">No posts yet</h3>
            <p className="text-sm text-cream-300">
              Be the first to create a post with this tag!
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <Link
                key={post.id}
                href={`/posts/${post.id}`}
                className="block card p-6 hover:border-sage-600 transition group"
              >
                <div className="flex gap-4">
                  {/* Vote Count */}
                  <div className="flex flex-col items-center gap-1 text-cream-200">
                    <div className="text-lg font-semibold">
                      {(post.upvote_count || 0) - (post.downvote_count || 0)}
                    </div>
                    <div className="text-xs text-cream-300">votes</div>
                  </div>

                  {/* Post Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-cream-100 group-hover:text-sage-400 transition mb-2">
                      {post.title}
                    </h3>
                    
                    {post.content_plain && (
                      <p className="text-sm text-cream-200 line-clamp-2 mb-3">
                        {post.content_plain.substring(0, 200)}...
                      </p>
                    )}

                    <div className="flex items-center gap-3 text-sm text-cream-300">
                      <span className="text-sage-400">{post.author_display_name || 'Unknown'}</span>
                      <span>•</span>
                      <span>{post.created_at_relative || formatTimeAgo(post.created_at)}</span>
                      {post.comment_count > 0 && (
                        <>
                          <span>•</span>
                          <span>{post.comment_count} comments</span>
                        </>
                      )}
                      {post.tags && post.tags.length > 1 && (
                        <>
                          <span>•</span>
                          <div className="flex gap-2">
                            {post.tags.filter((t: any) => t.name !== tagName).slice(0, 2).map((t: any) => (
                              <span key={t.id} className="px-2 py-0.5 bg-sage-600/20 border border-sage-600/40 rounded text-xs text-sage-300">
                                {t.name}
                              </span>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
