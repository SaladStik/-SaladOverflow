'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowLeft, ArrowUp, ArrowDown, MessageSquare, Share2, 
  Bookmark, Flag, Edit, Trash2, CheckCircle, Award, Calendar, Eye
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { formatTimeAgo } from '@/lib/utils';
import toast from 'react-hot-toast';
import MarkdownEditor from '@/components/MarkdownEditor';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

interface Post {
  id: number;
  title: string;
  content: string;
  post_type: 'question' | 'discussion' | 'announcement';
  author_id: number;
  author_display_name?: string;
  author_avatar?: string;
  author_is_verified?: boolean;
  tags: Array<{ id: number; name: string }>;
  upvote_count: number;
  downvote_count: number;
  comment_count: number;
  view_count: number;
  created_at: string;
  created_at_relative?: string;
  updated_at?: string;
  has_accepted_answer?: boolean;
  user_vote?: 'upvote' | 'downvote' | null;
  is_bookmarked?: boolean;
}

interface Comment {
  id: number;
  content: string;
  author_id: number;
  author_display_name?: string;
  author_avatar?: string;
  author_is_verified?: boolean;
  upvote_count: number;
  downvote_count: number;
  is_answer: boolean;
  is_accepted: boolean;
  created_at: string;
  user_vote?: 'upvote' | 'downvote' | null;
  parent_id?: number | null;
  replies?: Comment[];
  reply_count?: number;
}

export default function PostDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentContent, setCommentContent] = useState('');
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [replyContent, setReplyContent] = useState<{[key: number]: string}>({});
  const hasLoadedRef = useRef(false);

  const postId = parseInt(params.id as string);

  useEffect(() => {
    if (post?.title) {
      document.title = `${post.title} - SaladOverflow`;
    }
  }, [post?.title]);

  useEffect(() => {
    if (postId && !hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadPost();
      loadComments();
    }
  }, [postId]);

  const loadPost = async () => {
    try {
      const data = await api.getPost(postId);
      console.log('Post data received:', data);
      console.log('Post created_at:', data.created_at);
      console.log('Current time:', new Date().toISOString());
      console.log('Post time parsed:', new Date(data.created_at).toISOString());
      
      // Check if author data is missing
      if (!data.author_display_name) {
        console.error('Post is missing author data:', data);
        toast.error('Warning: Post author information is incomplete');
      }
      
      setPost(data);
      
      // Set bookmark status if available
      if (typeof data.is_bookmarked === 'boolean') {
        setIsBookmarked(data.is_bookmarked);
      }
    } catch (error: any) {
      console.error('Error loading post:', error);
      if (error.response?.status === 404) {
        toast.error('Post not found');
      } else {
        toast.error('Failed to load post');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadComments = async () => {
    try {
      const data = await api.getComments(postId);
      console.log('Comments data received:', data);
      setComments(data);
    } catch (error) {
      console.error('Error loading comments:', error);
    }
  };

  const handleVote = async (voteType: 'upvote' | 'downvote') => {
    if (!isAuthenticated) {
      toast.error('Please sign in to vote');
      return;
    }

    try {
      await api.votePost(postId, voteType);
      await loadPost(); // Reload to get updated vote count
      toast.success('Vote recorded');
    } catch (error) {
      console.error('Error voting:', error);
      toast.error('Failed to vote');
    }
  };

  const handleCommentVote = async (commentId: number, voteType: 'upvote' | 'downvote') => {
    if (!isAuthenticated) {
      toast.error('Please sign in to vote');
      return;
    }

    try {
      await api.voteComment(commentId, voteType);
      await loadComments();
      toast.success('Vote recorded');
    } catch (error) {
      console.error('Error voting:', error);
      toast.error('Failed to vote');
    }
  };

  const handleAcceptAnswer = async (commentId: number) => {
    if (!isAuthenticated) {
      toast.error('Please sign in to accept answers');
      return;
    }

    try {
      const result = await api.acceptAnswer(postId, commentId);
      await loadComments();
      await loadPost(); // Reload to update accepted answer status
      
      if (result.is_accepted) {
        toast.success('Answer accepted');
      } else {
        toast.success('Answer unaccepted');
      }
    } catch (error: any) {
      console.error('Error accepting answer:', error);
      
      let errorMsg = 'Failed to accept answer';
      if (error.response?.status === 403) {
        errorMsg = 'Only the post author can accept answers';
      } else if (error.response?.status === 400) {
        errorMsg = error.response.data?.detail || 'Only questions can have accepted answers';
      }
      
      toast.error(errorMsg);
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isAuthenticated) {
      toast.error('Please sign in to comment');
      return;
    }

    if (!commentContent.trim()) {
      toast.error('Please enter a comment');
      return;
    }

    setIsSubmittingComment(true);

    try {
      await api.createComment(postId, {
        content: commentContent.trim(),
        is_answer: post?.post_type === 'question',
      });

      setCommentContent('');
      await loadComments();
      await loadPost(); // Reload to update comment count
      toast.success('Comment added');
    } catch (error: any) {
      console.error('Error creating comment:', error);
      
      // Handle validation errors from backend
      let errorMsg = 'Failed to add comment';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          errorMsg = detail.map((err: any) => err.msg || err.message).join(', ');
        } else if (typeof detail === 'string') {
          errorMsg = detail;
        }
      }
      
      toast.error(errorMsg);
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const handleSubmitReply = async (commentId: number) => {
    if (!isAuthenticated) {
      toast.error('Please sign in to reply');
      return;
    }

    const content = replyContent[commentId];
    if (!content || !content.trim()) {
      toast.error('Please enter a reply');
      return;
    }

    try {
      await api.createComment(postId, {
        content: content.trim(),
        parent_id: commentId,
        is_answer: false, // Replies are never answers
      });

      // Clear reply content and close reply form
      setReplyContent(prev => ({ ...prev, [commentId]: '' }));
      setReplyingTo(null);
      
      await loadComments();
      await loadPost(); // Reload to update comment count
      toast.success('Reply added');
    } catch (error: any) {
      console.error('Error creating reply:', error);
      
      let errorMsg = 'Failed to add reply';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          errorMsg = detail.map((err: any) => err.msg || err.message).join(', ');
        } else if (typeof detail === 'string') {
          errorMsg = detail;
        }
      }
      
      toast.error(errorMsg);
    }
  };

  const handleBookmark = async () => {
    if (!isAuthenticated) {
      toast.error('Please sign in to bookmark posts');
      return;
    }

    try {
      const result = await api.toggleBookmark(postId);
      setIsBookmarked(result.is_bookmarked);
      toast.success(result.message);
    } catch (error) {
      console.error('Error toggling bookmark:', error);
      toast.error('Failed to bookmark post');
    }
  };

  const handleShare = async () => {
    const url = window.location.href;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: post?.title,
          url: url
        });
        toast.success('Shared successfully');
      } catch (error) {
        // User cancelled share
      }
    } else {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(url);
        toast.success('Link copied to clipboard');
      } catch (error) {
        toast.error('Failed to copy link');
      }
    }
  };

  const handleEdit = () => {
    router.push(`/posts/${postId}/edit`);
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
      return;
    }

    setIsDeleting(true);
    try {
      await api.deletePost(postId);
      toast.success('Post deleted successfully');
      router.push('/feed');
    } catch (error: any) {
      console.error('Error deleting post:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete post');
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-400"></div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-sage-100 mb-2">Post Not Found</h1>
          <p className="text-sage-400 mb-6">The post you're looking for doesn't exist.</p>
          <Link href="/feed" className="btn-primary">
            Back to Feed
          </Link>
        </div>
      </div>
    );
  }

  const isAuthor = user?.id === post?.author_id;
  const isQuestion = post?.post_type === 'question';
  const isAnnouncement = post?.post_type === 'announcement';
  
  // Determine terminology based on post type
  const commentLabel = isQuestion ? 'Suggestion' : 'Comment';
  const commentsLabel = isQuestion ? 'Suggestions' : 'Comments';
  const placeholderText = isQuestion ? 'Write your suggestion here...' : 'Write your comment here...';
  const submitButtonText = isQuestion ? 'Post Suggestion' : 'Post Comment';
  const emptyStateText = isQuestion ? 'No answers yet. Be the first to answer!' : 'No comments yet. Be the first to comment!';

  // Recursive component to render a comment and all its nested replies
  const renderComment = (comment: Comment, depth: number = 0) => {
    const isTopLevel = depth === 0;
    const indentClass = depth > 0 ? 'ml-9' : '';
    const bgClass = depth === 0 ? '' : depth === 1 ? 'bg-sage-700/10' : 'bg-sage-700/5';
    const paddingClass = depth === 0 ? 'p-6' : depth === 1 ? 'p-4' : 'p-3';
    const borderClass = depth > 0 ? 'border-l-2 border-sage-700/30 pl-4' : '';
    
    return (
      <div key={comment.id} className={indentClass}>
        <div className={`card ${paddingClass} ${bgClass} ${comment.is_accepted && isTopLevel ? 'ring-2 ring-sage-500' : ''}`}>
          {comment.is_accepted && isTopLevel && (
            <div className="flex items-center gap-2 text-sage-400 mb-4">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Accepted Answer</span>
            </div>
          )}

          <div className="flex gap-4">
            {/* Voting */}
            <div className="flex flex-col items-center gap-2">
              <button
                onClick={() => handleCommentVote(comment.id, 'upvote')}
                className={`p-1 rounded transition ${
                  comment.user_vote === 'upvote'
                    ? 'text-sage-300'
                    : 'text-sage-400 hover:text-sage-300'
                }`}
              >
                <ArrowUp className={`${depth === 0 ? 'w-5 h-5' : 'w-4 h-4'}`} />
              </button>
              <span className={`${depth === 0 ? 'text-sm' : 'text-xs'} font-bold text-sage-200`}>
                {(comment.upvote_count || 0) - (comment.downvote_count || 0)}
              </span>
              <button
                onClick={() => handleCommentVote(comment.id, 'downvote')}
                className={`p-1 rounded transition ${
                  comment.user_vote === 'downvote'
                    ? 'text-red-400'
                    : 'text-sage-400 hover:text-red-400'
                }`}
              >
                <ArrowDown className={`${depth === 0 ? 'w-5 h-5' : 'w-4 h-4'}`} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1">
              <div className={`prose ${depth === 0 ? 'prose-base' : 'prose-sm'} prose-invert prose-slate max-w-none prose-pre:bg-charcoal-400 prose-pre:border prose-pre:border-sage-700 prose-code:text-sage-300 prose-headings:text-cream-100 prose-p:text-cream-200 prose-li:text-cream-200 prose-strong:text-cream-100 prose-a:text-sage-400 prose-a:underline prose-a:decoration-2 mb-4`}>
                <div dangerouslySetInnerHTML={{ __html: comment.content }} />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-sage-400">
                  <Link 
                    href={`/@${comment.author_display_name}`}
                    className="flex items-center gap-2 hover:text-sage-300 transition"
                  >
                    <div className={`${depth === 0 ? 'w-6 h-6' : 'w-5 h-5'} rounded-full bg-gradient-to-br from-sage-500 to-sage-700 flex items-center justify-center overflow-hidden shadow-lg shadow-sage-600/40`}>
                      {comment.author_avatar ? (
                        <img src={comment.author_avatar} alt={comment.author_display_name} className="w-full h-full object-cover" />
                      ) : (
                        <span className={`${depth === 0 ? 'text-xs' : 'text-xs'} font-bold text-cream-100`}>
                          {comment.author_display_name?.[0]?.toUpperCase() || '?'}
                        </span>
                      )}
                    </div>
                    <span className={`${depth === 0 ? 'text-sm' : 'text-xs'} font-medium text-cream-200`}>{comment.author_display_name || 'Unknown'}</span>
                  </Link>
                  <span>•</span>
                  <span className={depth === 0 ? 'text-sm' : 'text-xs'}>{formatTimeAgo(comment.created_at)}</span>
                </div>
                
                {/* Accept Answer Button - Only show for post author on questions at top level */}
                {isAuthor && isQuestion && isTopLevel && (
                  <button
                    onClick={() => handleAcceptAnswer(comment.id)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                      comment.is_accepted
                        ? 'bg-sage-500/30 text-sage-300 border-2 border-sage-500 hover:bg-sage-500/40'
                        : 'bg-charcoal-400 text-sage-300 border-2 border-sage-600 hover:bg-charcoal-300'
                    }`}
                  >
                    <CheckCircle className={`w-4 h-4 ${comment.is_accepted ? 'fill-current' : ''}`} />
                    {comment.is_accepted ? 'Accepted' : 'Mark as Answer'}
                  </button>
                )}
              </div>

              {/* Reply Button */}
              {isAuthenticated && replyingTo !== comment.id && (
                <button
                  onClick={() => setReplyingTo(comment.id)}
                  className={`mt-2 ${depth === 0 ? 'text-sm' : 'text-xs'} text-sage-400 hover:text-sage-300 transition inline-flex items-center gap-1`}
                >
                  <MessageSquare className="w-4 h-4" />
                  Reply
                </button>
              )}

              {/* Reply Form */}
              {replyingTo === comment.id && (
                <div className="mt-3">
                  <MarkdownEditor
                    value={replyContent[comment.id] || ''}
                    onChange={(value) => setReplyContent(prev => ({ ...prev, [comment.id]: value }))}
                    placeholder="Write your reply here..."
                    minHeight={depth === 0 ? "min-h-[100px]" : "min-h-[80px]"}
                    label={depth === 0 ? "Your Reply" : undefined}
                  />
                  <div className="flex justify-end gap-2 mt-2">
                    <button
                      onClick={() => setReplyingTo(null)}
                      className={`px-3 ${depth === 0 ? 'py-2' : 'py-1.5'} text-sm text-sage-400 hover:text-sage-300 rounded-lg transition`}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSubmitReply(comment.id)}
                      disabled={!replyContent[comment.id]?.trim()}
                      className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Reply
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recursively render nested replies */}
        {comment.replies && comment.replies.length > 0 && (
          <div className={`mt-3 space-y-3 ${borderClass}`}>
            {comment.replies.map((reply) => renderComment(reply, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <Link
          href="/feed"
          className="inline-flex items-center gap-2 text-sage-400 hover:text-sage-300 mb-6 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Feed
        </Link>

        {/* Main Content */}
        <div className="grid grid-cols-12 gap-6">
          {/* Voting Sidebar */}
          <div className="col-span-1">
            <div className="sticky top-24 flex flex-col items-center gap-2">
              <button
                onClick={() => handleVote('upvote')}
                className={`p-2 rounded-lg transition ${
                  post?.user_vote === 'upvote'
                    ? 'text-sage-300 bg-sage-600/30 border-2 border-sage-500'
                    : 'text-sage-400 hover:text-sage-300 hover:bg-sage-600/20 border-2 border-transparent'
                }`}
              >
                <ArrowUp className="w-6 h-6" />
              </button>
              <span className="text-lg font-bold text-sage-200">
                {(post?.upvote_count || 0) - (post?.downvote_count || 0)}
              </span>
              <button
                onClick={() => handleVote('downvote')}
                className={`p-2 rounded-lg transition ${
                  post?.user_vote === 'downvote'
                    ? 'text-red-400 bg-red-500/20 border-2 border-red-500'
                    : 'text-sage-400 hover:text-red-400 hover:bg-sage-600/20 border-2 border-transparent'
                }`}
              >
                <ArrowDown className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Post Content */}
          <div className="col-span-11">
            <div className="card p-8">
              {/* Post Header */}
              <div className="mb-6">
                {/* Post Type Badge */}
                <div className="flex items-center gap-3 mb-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    post?.post_type === 'question' 
                      ? 'bg-sage-600/30 text-sage-200 border-2 border-sage-500/50 shadow-lg shadow-sage-600/20'
                      : post?.post_type === 'discussion'
                      ? 'bg-sage-700/40 text-sage-200 border-2 border-sage-600/50 shadow-lg shadow-sage-700/20'
                      : 'bg-sage-600/30 text-sage-200 border-2 border-sage-500/50 shadow-lg shadow-sage-600/20'
                  }`}>
                    {post?.post_type?.charAt(0).toUpperCase() + post?.post_type?.slice(1)}
                  </span>
                  {post?.has_accepted_answer && (
                    <span className="flex items-center gap-1 px-3 py-1 bg-sage-600/30 text-sage-200 border-2 border-sage-500/50 shadow-lg shadow-sage-600/20 rounded-full text-xs font-medium">
                      <CheckCircle className="w-3 h-3" />
                      Answered
                    </span>
                  )}
                </div>

                <h1 className="text-3xl font-bold text-sage-100 mb-4">{post?.title}</h1>

                {/* Meta Info */}
                <div className="flex items-center gap-4 text-sm text-sage-400">
                  <Link 
                    href={`/@${post?.author_display_name}`}
                    className="flex items-center gap-2 hover:text-sage-300 transition"
                  >
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-sage-500 to-sage-700 flex items-center justify-center overflow-hidden shadow-lg shadow-sage-600/40">
                      {post?.author_avatar ? (
                        <img 
                          src={post?.author_avatar} 
                          alt={post?.author_display_name || 'User'} 
                          className="w-full h-full object-cover" 
                        />
                      ) : (
                        <span className="text-xs font-bold text-cream-100">
                          {post?.author_display_name?.[0]?.toUpperCase() || '?'}
                        </span>
                      )}
                    </div>
                    <span className="font-medium">{post?.author_display_name || 'Unknown'}</span>
                    {post?.author_is_verified && <CheckCircle className="w-4 h-4 text-sage-400" />}
                  </Link>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {post?.created_at_relative || (post?.created_at ? formatTimeAgo(post.created_at) : 'Unknown')}
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {post?.view_count} views
                  </span>
                </div>
              </div>

              {/* Post Content */}
              <div className="prose prose-invert prose-slate max-w-none mb-6">
                <div 
                  className="text-sage-300" 
                  dangerouslySetInnerHTML={{ __html: post?.content || '' }}
                />
              </div>

              {/* Tags */}
              {post?.tags && post.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-6">
                  {post.tags.map((tag) => (
                    <Link
                      key={tag.id}
                      href={`/tags/${tag.name}`}
                      className="px-3 py-1 bg-sage-600/20 text-sage-300 border-2 border-sage-600/40 hover:bg-sage-600/30 hover:border-sage-500 rounded-full text-sm transition"
                    >
                      #{tag.name}
                    </Link>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-4 pt-4 border-t-2 border-sage-700/40">
                <button 
                  onClick={handleShare}
                  className="flex items-center gap-2 px-3 py-2 text-sage-400 hover:text-sage-300 hover:bg-sage-600/20 rounded-lg transition"
                >
                  <Share2 className="w-4 h-4" />
                  Share
                </button>
                <button 
                  onClick={handleBookmark}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${
                    isBookmarked
                      ? 'text-sage-400 bg-sage-600/20 border-2 border-sage-500'
                      : 'text-sage-400 hover:text-sage-300 hover:bg-sage-600/20'
                  }`}
                >
                  <Bookmark className={`w-4 h-4 ${isBookmarked ? 'fill-current' : ''}`} />
                  {isBookmarked ? 'Saved' : 'Save'}
                </button>
                {isAuthor && (
                  <>
                    <button 
                      onClick={handleEdit}
                      className="flex items-center gap-2 px-3 py-2 text-sage-400 hover:text-sage-300 hover:bg-sage-600/20 rounded-lg transition"
                    >
                      <Edit className="w-4 h-4" />
                      Edit
                    </button>
                    <button 
                      onClick={handleDelete}
                      className="flex items-center gap-2 px-3 py-2 text-sage-400 hover:text-red-400 hover:bg-sage-600/20 rounded-lg transition"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </>
                )}
                {!isAuthor && (
                  <button className="flex items-center gap-2 px-3 py-2 text-sage-400 hover:text-red-400 hover:bg-sage-600/20 rounded-lg transition ml-auto">
                    <Flag className="w-4 h-4" />
                    Report
                  </button>
                )}
              </div>
            </div>

            {/* Comments Section */}
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-sage-100 mb-6">
                {post?.comment_count} {post?.comment_count === 1 ? commentLabel : commentsLabel}
              </h2>

              {/* Add Comment Form */}
              {isAuthenticated ? (
                <form onSubmit={handleSubmitComment} className="card p-6 mb-6">
                  <MarkdownEditor
                    value={commentContent}
                    onChange={setCommentContent}
                    placeholder={placeholderText}
                    minHeight="min-h-[150px]"
                    label={`Your ${commentLabel}`}
                  />
                  <div className="flex justify-end mt-4">
                    <button
                      type="submit"
                      disabled={isSubmittingComment || !commentContent.trim()}
                      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSubmittingComment ? 'Posting...' : submitButtonText}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="card p-6 mb-6 text-center">
                  <p className="text-sage-400 mb-4">Sign in to post a {commentLabel.toLowerCase()}</p>
                  <Link href="/auth/signin" className="btn-primary inline-block">
                    Sign In
                  </Link>
                </div>
              )}

              {/* Comments List */}
              <div className="space-y-4">
                {comments.map((comment) => renderComment(comment))}

                {comments.length === 0 && (
                  <div className="card p-12 text-center">
                    <MessageSquare className="w-16 h-16 text-sage-700 mx-auto mb-4" />
                    <p className="text-sage-400">{emptyStateText}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
