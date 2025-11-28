'use client';

import React, { useRef, useState } from 'react';
import { Bold, Italic, Code, List, Link2, Image as ImageIcon, Eye } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minHeight?: string;
  label?: string;
}

export default function MarkdownEditor({ 
  value, 
  onChange, 
  placeholder = "Write your content here... Markdown is supported!",
  minHeight = "min-h-[200px]",
  label
}: MarkdownEditorProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Markdown formatting helpers
  const insertMarkdown = (before: string, after: string = '', placeholder: string = 'text') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end) || placeholder;
    const newText = value.substring(0, start) + before + selectedText + after + value.substring(end);
    
    onChange(newText);
    
    setTimeout(() => {
      textarea.focus();
      const newPos = start + before.length + selectedText.length;
      textarea.setSelectionRange(newPos, newPos);
    }, 0);
  };

  const insertBold = () => insertMarkdown('**', '**', 'bold text');
  const insertItalic = () => insertMarkdown('*', '*', 'italic text');
  const insertCode = () => insertMarkdown('`', '`', 'code');
  const insertList = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const lineStart = value.lastIndexOf('\n', start - 1) + 1;
    const newText = value.substring(0, lineStart) + '- ' + value.substring(lineStart);
    onChange(newText);
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

      const textarea = textareaRef.current;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = value.substring(start, end) || file.name.replace(/\.[^/.]+$/, '');
        const newText = value.substring(0, start) + `![${selectedText}](${imageUrl})` + value.substring(end);
        onChange(newText);
        
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

  return (
    <div>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="hidden"
      />
      
      {label && (
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-cream-200">
            {label}
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
      )}

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
        <div className={`${minHeight} p-4 bg-charcoal-300 border-2 border-sage-700 rounded-lg prose prose-invert prose-slate max-w-none prose-pre:bg-charcoal-400 prose-pre:border prose-pre:border-sage-700 prose-code:text-sage-300 prose-headings:text-cream-100 prose-p:text-cream-200 prose-li:text-cream-200 prose-strong:text-cream-100 prose-a:text-sage-400`}>
          {value ? (
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
            >
              {value}
            </ReactMarkdown>
          ) : (
            <div className="text-cream-200/60 italic">Nothing to preview yet...</div>
          )}
        </div>
      ) : (
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full ${minHeight} px-4 py-3 bg-charcoal-300 border-2 border-sage-700 rounded-lg text-cream-100 placeholder-cream-200/50 focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent resize-y font-mono text-sm`}
        />
      )}

      <div className="text-sm text-cream-200/60 mt-2">
        Markdown formatting is supported
      </div>
    </div>
  );
}
