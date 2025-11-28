'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Hash, TrendingUp, Search, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { formatNumber } from '@/lib/utils';
import toast from 'react-hot-toast';

interface Tag {
  id: number;
  name: string;
  description?: string;
  post_count: number;
  created_at: string;
}

export default function TagsPage() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredTags, setFilteredTags] = useState<Tag[]>([]);

  useEffect(() => {
    document.title = 'Browse Tags - SaladOverflow';
    loadTags();
  }, []);

  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = tags.filter(tag =>
        tag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tag.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredTags(filtered);
    } else {
      setFilteredTags(tags);
    }
  }, [searchQuery, tags]);

  const loadTags = async () => {
    try {
      setLoading(true);
      const data = await api.getTags('', 100);
      // Sort by post count (most popular first)
      const sortedTags = data.sort((a: Tag, b: Tag) => b.post_count - a.post_count);
      setTags(sortedTags);
      setFilteredTags(sortedTags);
    } catch (error) {
      console.error('Failed to load tags:', error);
      toast.error('Failed to load tags');
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-gradient-to-br from-sage-500 to-sage-700 rounded-xl shadow-lg shadow-sage-600/40">
            <Hash className="w-8 h-8 text-cream-100" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-cream-100">Browse Tags</h1>
            <p className="text-sage-400 mt-1">
              Explore topics and find posts by tag
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-2xl">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-sage-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tags..."
            className="w-full pl-12 pr-4 py-3 bg-charcoal-400 border-2 border-sage-700/40 rounded-xl text-cream-100 placeholder-sage-500 focus:outline-none focus:border-sage-500 transition"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sage-600/20 rounded-lg">
              <Hash className="w-6 h-6 text-sage-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-cream-100">
                {formatNumber(tags.length)}
              </div>
              <div className="text-sm text-sage-400">Total Tags</div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sage-600/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-sage-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-cream-100">
                {formatNumber(tags.reduce((sum, tag) => sum + tag.post_count, 0))}
              </div>
              <div className="text-sm text-sage-400">Total Posts</div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sage-600/20 rounded-lg">
              <Sparkles className="w-6 h-6 text-sage-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-cream-100">
                {formatNumber(filteredTags.length)}
              </div>
              <div className="text-sm text-sage-400">
                {searchQuery ? 'Matching Tags' : 'Active Tags'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tags Grid */}
      {filteredTags.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTags.map((tag) => (
            <Link
              key={tag.id}
              href={`/tags/${tag.name}`}
              className="card p-6 hover:border-sage-500 hover:shadow-lg hover:shadow-sage-600/20 transition group"
            >
              <div className="flex items-start gap-3 mb-3">
                <div className="p-2 bg-sage-600/20 border-2 border-sage-600/40 rounded-lg group-hover:bg-sage-600/30 group-hover:border-sage-500/60 transition">
                  <Hash className="w-5 h-5 text-sage-400 group-hover:text-sage-300 transition" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-cream-100 group-hover:text-sage-300 transition truncate">
                    {tag.name}
                  </h3>
                </div>
              </div>

              {tag.description && (
                <p className="text-sm text-sage-400 mb-3 line-clamp-2">
                  {tag.description}
                </p>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-sage-400">
                  <span className="font-medium text-cream-200">
                    {formatNumber(tag.post_count)}
                  </span>
                  <span>
                    {tag.post_count === 1 ? 'post' : 'posts'}
                  </span>
                </div>
                <div className="text-xs text-sage-500 group-hover:text-sage-400 transition">
                  View tag →
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <Hash className="w-16 h-16 text-sage-700 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-cream-100 mb-2">
            No tags found
          </h3>
          <p className="text-sage-400">
            {searchQuery
              ? `No tags match "${searchQuery}". Try a different search term.`
              : 'No tags have been created yet.'}
          </p>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="mt-4 btn-secondary"
            >
              Clear search
            </button>
          )}
        </div>
      )}

      {/* Popular Tags Section */}
      {!searchQuery && tags.length > 0 && (
        <div className="mt-12">
          <h2 className="text-2xl font-bold text-cream-100 mb-6 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-sage-400" />
            Most Popular Tags
          </h2>
          <div className="flex flex-wrap gap-3">
            {tags.slice(0, 20).map((tag) => (
              <Link
                key={tag.id}
                href={`/tags/${tag.name}`}
                className="inline-flex items-center gap-2 px-4 py-2 bg-charcoal-400 border-2 border-sage-700/40 rounded-lg hover:border-sage-500 hover:bg-sage-600/10 transition group"
              >
                <Hash className="w-4 h-4 text-sage-400 group-hover:text-sage-300 transition" />
                <span className="text-cream-200 group-hover:text-cream-100 transition">
                  {tag.name}
                </span>
                <span className="text-xs text-sage-500 group-hover:text-sage-400 transition">
                  {formatNumber(tag.post_count)}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
