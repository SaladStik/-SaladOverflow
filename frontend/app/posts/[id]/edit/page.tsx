'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save, Eye, Code, Bold, Italic, List, Link2, Image as ImageIcon } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

interface Post {
  id: number;
  title: string;
  content: string;
  content_markdown?: string;
  post_type: 'question' | 'discussion' | 'announcement';
  author_id: number;
  tags: Array<{ id: number; name: string }>;
}

export default function EditPostPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const contentRef = React.useRef<HTMLTextAreaElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const postId = parseInt(params.id as string);

  useEffect(() => {
    if (post?.title) {
      document.title = `Edit: ${post.title} - SaladOverflow`;
    }
  }, [post?.title]);

  // Helper function to convert HTML back to Markdown for editing
  const htmlToMarkdown = (html: string): string => {
    let markdown = html;
    
    // Remove wrapping paragraph tags but keep content
    markdown = markdown.replace(/<p>([\s\S]*?)<\/p>/g, '$1\n\n');
    
    // Convert headings
    markdown = markdown.replace(/<h1>(.*?)<\/h1>/g, '# $1\n');
    markdown = markdown.replace(/<h2>(.*?)<\/h2>/g, '## $1\n');
    markdown = markdown.replace(/<h3>(.*?)<\/h3>/g, '### $1\n');
    markdown = markdown.replace(/<h4>(.*?)<\/h4>/g, '#### $1\n');
    markdown = markdown.replace(/<h5>(.*?)<\/h5>/g, '##### $1\n');
    markdown = markdown.replace(/<h6>(.*?)<\/h6>/g, '###### $1\n');
    
    // Convert strong/bold
    markdown = markdown.replace(/<strong>(.*?)<\/strong>/g, '**$1**');
    markdown = markdown.replace(/<b>(.*?)<\/b>/g, '**$1**');
    
    // Convert em/italic
    markdown = markdown.replace(/<em>(.*?)<\/em>/g, '*$1*');
    markdown = markdown.replace(/<i>(.*?)<\/i>/g, '*$1*');
    
    // Convert links
    markdown = markdown.replace(/<a href="(.*?)".*?>(.*?)<\/a>/g, '[$2]($1)');
    
    // Convert images
    markdown = markdown.replace(/<img src="(.*?)" alt="(.*?)".*?>/g, '![$2]($1)');
    markdown = markdown.replace(/<img src="(.*?)".*?>/g, '![]($1)');
    
    // Convert code blocks
    markdown = markdown.replace(/<pre><code class="language-(.*?)">([\s\S]*?)<\/code><\/pre>/g, '```$1\n$2\n```\n');
    markdown = markdown.replace(/<pre><code>([\s\S]*?)<\/code><\/pre>/g, '```\n$1\n```\n');
    
    // Convert inline code
    markdown = markdown.replace(/<code>(.*?)<\/code>/g, '`$1`');
    
    // Convert lists
    markdown = markdown.replace(/<ul>([\s\S]*?)<\/ul>/g, (match, content) => {
      return content.replace(/<li>(.*?)<\/li>/g, '- $1\n');
    });
    markdown = markdown.replace(/<ol>([\s\S]*?)<\/ol>/g, (match, content) => {
      let counter = 1;
      return content.replace(/<li>(.*?)<\/li>/g, () => `${counter++}. $1\n`);
    });
    
    // Convert blockquotes
    markdown = markdown.replace(/<blockquote>([\s\S]*?)<\/blockquote>/g, (match, content) => {
      return content.split('\n').map((line: string) => `> ${line}`).join('\n') + '\n';
    });
    
    // Convert line breaks
    markdown = markdown.replace(/<br\s*\/?>/g, '\n');
    
    // Remove any remaining HTML tags
    markdown = markdown.replace(/<\/?[^>]+(>|$)/g, '');
    
    // Decode HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = markdown;
    markdown = textarea.value;
    
    // Clean up excessive newlines
    markdown = markdown.replace(/\n{3,}/g, '\n\n');
    markdown = markdown.trim();
    
    return markdown;
  };

  // Load post data
  useEffect(() => {
    const loadPost = async () => {
      try {
        const data = await api.getPost(postId);
        setPost(data);
        
        // Check authorization - only author can edit
        if (user && data.author_id !== user.id) {
          toast.error('You can only edit your own posts');
          router.push(`/posts/${postId}`);
          return;
        }
        
        // Set form values
        setTitle(data.title);
        // Use original markdown if available, otherwise convert HTML back to markdown
        if (data.content_markdown) {
          setContent(data.content_markdown);
        } else {
          setContent(htmlToMarkdown(data.content));
        }
        setTags(data.tags.map((tag: any) => tag.name).join(', '));
        
        setLoading(false);
      } catch (error: any) {
        console.error('Error loading post:', error);
        toast.error('Failed to load post');
        router.push('/feed');
      }
    };

    if (postId && isAuthenticated) {
      loadPost();
    }
  }, [postId, isAuthenticated, user, router]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      toast.error('Please sign in to edit posts');
      router.push('/auth/signin');
    }
  }, [isAuthenticated, router]);

  // Markdown formatting helpers
  const insertMarkdown = (before: string, after: string = '', placeholder: string = 'text') => {
    const textarea = contentRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = content.substring(start, end) || placeholder;
    const newText = content.substring(0, start) + before + selectedText + after + content.substring(end);
    
    setContent(newText);
    
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

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be smaller than 5MB');
      return;
    }

    setIsUploading(true);
    const uploadToast = toast.loading('Uploading image...');

    try {
      const response = await api.uploadImage(file);
      const imageUrl = response.url;

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
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const insertImage = () => {
    fileInputRef.current?.click();
  };

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
      
      await api.updatePost(postId, {
        title: title.trim(),
        content: content.trim(),
        tags: tagArray,
      });

      toast.success('Post updated successfully!');
      router.push(`/posts/${postId}`);
    } catch (error: any) {
      console.error('Error updating post:', error);
      
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
        toast.error('Failed to update post');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isAuthenticated || loading) {
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
          <p className="text-sage-400 mb-6">The post you're trying to edit doesn't exist.</p>
          <Link href="/feed" className="btn-primary">
            Back to Feed
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/posts/${postId}`}
            className="inline-flex items-center gap-2 text-sage-400 hover:text-sage-300 mb-4 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Post
          </Link>
          <h1 className="text-3xl font-bold text-cream-100">Edit Post</h1>
          <p className="text-cream-200 mt-2">
            Make changes to your post
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

          {/* Post Type Display (read-only) */}
          <div className="card p-6">
            <label className="block text-sm font-medium text-cream-200 mb-3">
              Post Type
            </label>
            <div className="px-4 py-3 bg-charcoal-300 border-2 border-sage-700 rounded-lg text-cream-100">
              {post.post_type.charAt(0).toUpperCase() + post.post_type.slice(1)}
            </div>
            <div className="text-sm text-cream-200/60 mt-2">
              Post type cannot be changed after creation
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
              Add up to 5 tags to help others find your post
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex items-center justify-end gap-4">
            <Link
              href={`/posts/${postId}`}
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
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
