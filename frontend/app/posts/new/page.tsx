'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Send, Eye, Code, Bold, Italic, List, Link2, Image as ImageIcon } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

export default function NewPostPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [postType, setPostType] = useState<'question' | 'discussion' | 'announcement'>('question');
  const [showPreview, setShowPreview] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const contentRef = React.useRef<HTMLTextAreaElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    document.title = 'Create Post - SaladOverflow';
  }, []);

  // Markdown formatting helpers
  const insertMarkdown = (before: string, after: string = '', placeholder: string = 'text') => {
    const textarea = contentRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = content.substring(start, end) || placeholder;
    const newText = content.substring(0, start) + before + selectedText + after + content.substring(end);
    
    setContent(newText);
    
    // Set cursor position after insertion
    setTimeout(() => {
      textarea.focus();
      const newPos = start + before.length + selectedText.length;
      textarea.setSelectionRange(newPos, newPos);
    }, 0);
  };

  const insertBold = () => insertMarkdown('**', '**', 'bold text');
  const insertItalic = () => insertMarkdown('*', '*', 'italic text');
  const insertCode = () => insertMarkdown('`', '`', 'code');
  const insertCodeBlock = () => insertMarkdown('\n```\n', '\n```\n', 'code block');
  const insertList = () => {
    const textarea = contentRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const lineStart = content.lastIndexOf('\n', start - 1) + 1;
    const newText = content.substring(0, lineStart) + '- ' + content.substring(lineStart);
    setContent(newText);
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + 2, start + 2);
    }, 0);
  };
  const insertLink = () => insertMarkdown('[', '](url)', 'link text');
  
  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be smaller than 5MB');
      return;
    }

    setIsUploading(true);
    const uploadToast = toast.loading('Uploading image...');

    try {
      const response = await api.uploadImage(file);
      const imageUrl = response.url;

      // Insert markdown image syntax with uploaded URL
      const textarea = contentRef.current;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = content.substring(start, end) || file.name.replace(/\.[^/.]+$/, '');
        const newText = content.substring(0, start) + `![${selectedText}](${imageUrl})` + content.substring(end);
        setContent(newText);
        
        setTimeout(() => {
          textarea.focus();
          const newPos = start + selectedText.length + imageUrl.length + 5;
          textarea.setSelectionRange(newPos, newPos);
        }, 0);
      }

      toast.success('Image uploaded successfully!', { id: uploadToast });
    } catch (error: any) {
      console.error('Error uploading image:', error);
      toast.error('Failed to upload image', { id: uploadToast });
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const insertImage = () => {
    fileInputRef.current?.click();
  };

  // Redirect if not authenticated
  React.useEffect(() => {
    if (!isAuthenticated) {
      toast.error('Please sign in to create a post');
      router.push('/auth/signin');
    }
  }, [isAuthenticated, router]);

  const formatValidationError = (field: string, message: string): string => {
    const friendlyMessages: Record<string, (msg: string) => string> = {
      'body.title': (msg) => {
        if (msg.includes('at least 10 characters')) {
          return 'Title must be at least 10 characters long';
        }
        return 'Title is invalid';
      },
      'body.content': (msg) => {
        if (msg.includes('at least 10 characters')) {
          return 'Content must be at least 10 characters long';
        }
        return 'Content is invalid';
      },
      'body.tags': (msg) => {
        if (msg.includes('at least 1 item')) {
          return 'Please add at least one tag';
        }
        if (msg.includes('at most 5 items')) {
          return 'You can add a maximum of 5 tags';
        }
        return 'Tags are invalid';
      },
    };

    const formatter = friendlyMessages[field];
    return formatter ? formatter(message) : message;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      toast.error('Please enter a title');
      return;
    }

    if (!content.trim()) {
      toast.error('Please enter some content');
      return;
    }

    setIsSubmitting(true);

    try {
      const tagArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
      
      const newPost = await api.createPost({
        title: title.trim(),
        content: content.trim(),
        post_type: postType,
        tags: tagArray,
      });

      toast.success('Post created successfully!');
      router.push(`/posts/${newPost.id}`);
    } catch (error: any) {
      console.error('Error creating post:', error);
      console.error('Error response:', error.response?.data);
      
      // Handle validation errors
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Pydantic validation errors - format them in a user-friendly way
          const errors = error.response.data.detail
            .map((err: any) => {
              const field = err.loc.join('.');
              return formatValidationError(field, err.msg);
            })
            .filter((msg: string, index: number, self: string[]) => self.indexOf(msg) === index); // Remove duplicates
          
          // Display each error separately for better readability
          errors.forEach((errorMsg: string) => {
            toast.error(errorMsg);
          });
        } else {
          toast.error(error.response.data.detail);
        }
      } else {
        toast.error('Failed to create post');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-400"></div>
      </div>
    );
  }

  return (
    <div>
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
          <h1 className="text-3xl font-bold text-cream-100">Create a New Post</h1>
          <p className="text-cream-200 mt-2">
            Share your knowledge, ask questions, or start a discussion
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Hidden file input for images */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />

          {/* Post Type Selection */}
          <div className="card p-6">
            <label className="block text-sm font-medium text-cream-200 mb-3">
              Post Type
            </label>
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => setPostType('question')}
                className={`flex-1 p-4 rounded-lg border-2 transition ${
                  postType === 'question'
                    ? 'border-sage-400 bg-sage-600/30 shadow-lg shadow-sage-600/30'
                    : 'border-sage-700 hover:border-sage-600 hover:bg-sage-700/20'
                }`}
              >
                <div className="text-left">
                  <div className="font-semibold text-cream-100">Question</div>
                  <div className="text-sm text-cream-200 mt-1">
                    Ask for help or solutions
                  </div>
                </div>
              </button>
              <button
                type="button"
                onClick={() => setPostType('discussion')}
                className={`flex-1 p-4 rounded-lg border-2 transition ${
                  postType === 'discussion'
                    ? 'border-sage-400 bg-sage-600/30 shadow-lg shadow-sage-600/30'
                    : 'border-sage-700 hover:border-sage-600 hover:bg-sage-700/20'
                }`}
              >
                <div className="text-left">
                  <div className="font-semibold text-cream-100">Discussion</div>
                  <div className="text-sm text-cream-200 mt-1">
                    Start a conversation
                  </div>
                </div>
              </button>
              <button
                type="button"
                onClick={() => setPostType('announcement')}
                className={`flex-1 p-4 rounded-lg border-2 transition ${
                  postType === 'announcement'
                    ? 'border-sage-400 bg-sage-600/30 shadow-lg shadow-sage-600/30'
                    : 'border-sage-700 hover:border-sage-600 hover:bg-sage-700/20'
                }`}
              >
                <div className="text-left">
                  <div className="font-semibold text-cream-100">Announcement</div>
                  <div className="text-sm text-cream-200 mt-1">
                    Share news or updates
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Title */}
          <div className="card p-6">
            <label htmlFor="title" className="block text-sm font-medium text-cream-200 mb-3">
              Title
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a descriptive title..."
              className="w-full px-4 py-3 bg-charcoal-300 border-2 border-sage-600 rounded-lg text-cream-100 placeholder-cream-200/50 focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              maxLength={200}
            />
            <div className="text-sm text-cream-200/60 mt-2 text-right">
              {title.length}/200 characters
            </div>
          </div>

          {/* Content Editor */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-3">
              <label htmlFor="content" className="block text-sm font-medium text-cream-200">
                Content
              </label>
              <button
                type="button"
                onClick={() => setShowPreview(!showPreview)}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-cream-200 hover:text-sage-400 hover:bg-sage-600/20 rounded-lg transition"
              >
                {showPreview ? (
                  <>
                    <Code className="w-4 h-4" />
                    Edit
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4" />
                    Preview
                  </>
                )}
              </button>
            </div>

            {/* Markdown Toolbar */}
            {!showPreview && (
              <div className="flex items-center gap-2 mb-3 p-2 bg-charcoal-300 border-2 border-sage-700 rounded-lg">
                <button
                  type="button"
                  onClick={insertBold}
                  className="p-2 text-cream-200 hover:text-sage-400 hover:bg-sage-600/20 rounded transition"
                  title="Bold"
                >
                  <Bold className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={insertItalic}
                  className="p-2 text-cream-200 hover:text-sage-400 hover:bg-sage-600/20 rounded transition"
                  title="Italic"
                >
                  <Italic className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={insertCode}
                  className="p-2 text-cream-200 hover:text-sage-400 hover:bg-sage-600/20 rounded transition"
                  title="Inline Code"
                >
                  <Code className="w-4 h-4" />
                </button>
                <div className="w-px h-6 bg-sage-700"></div>
                <button
                  type="button"
                  onClick={insertList}
                  className="p-2 text-cream-200 hover:text-sage-400 hover:bg-sage-600/20 rounded transition"
                  title="List"
                >
                  <List className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={insertLink}
                  className="p-2 text-cream-200 hover:text-sage-400 hover:bg-sage-600/20 rounded transition"
                  title="Link"
                >
                  <Link2 className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={insertImage}
                  disabled={isUploading}
                  className="p-2 text-cream-200 hover:text-sage-400 hover:bg-sage-600/20 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Upload Image"
                >
                  {isUploading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-sage-400"></div>
                  ) : (
                    <ImageIcon className="w-4 h-4" />
                  )}
                </button>
              </div>
            )}

            {showPreview ? (
              <div className="min-h-[300px] p-4 bg-charcoal-300 border-2 border-sage-700 rounded-lg prose prose-invert prose-slate max-w-none prose-pre:bg-charcoal-400 prose-pre:border prose-pre:border-sage-700 prose-code:text-sage-300 prose-headings:text-cream-100 prose-p:text-cream-200 prose-li:text-cream-200 prose-strong:text-cream-100 prose-a:text-sage-400">
                {content ? (
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                  >
                    {content}
                  </ReactMarkdown>
                ) : (
                  <div className="text-cream-200/60 italic">Nothing to preview yet...</div>
                )}
              </div>
            ) : (
              <textarea
                ref={contentRef}
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write your post content here... Markdown is supported!"
                className="w-full min-h-[300px] px-4 py-3 bg-charcoal-300 border-2 border-sage-700 rounded-lg text-cream-100 placeholder-cream-200/50 focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent resize-y font-mono text-sm"
              />
            )}

            <div className="text-sm text-cream-200/60 mt-2">
              Markdown formatting is supported
            </div>
          </div>

          {/* Tags */}
          <div className="card p-6">
            <label htmlFor="tags" className="block text-sm font-medium text-cream-200 mb-3">
              Tags
            </label>
            <input
              id="tags"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="javascript, react, next.js (comma-separated)"
              className="w-full px-4 py-3 bg-charcoal-300 border-2 border-sage-700 rounded-lg text-cream-100 placeholder-cream-200/50 focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            />
            <div className="text-sm text-cream-200/60 mt-2">
              Add 1-5 tags to help others find your post
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex items-center justify-end gap-4">
            <Link
              href="/feed"
              className="btn-secondary"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim() || !content.trim()}
              className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Publishing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Publish Post
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
