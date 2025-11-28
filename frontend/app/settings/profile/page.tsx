'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowLeft, Upload, X, Save, MapPin, Link2, 
  Twitter, Github, Linkedin, User, Mail, FileText
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import toast from 'react-hot-toast';
import ImageCropModal from '@/components/ImageCropModal';

export default function ProfileSettingsPage() {
  const router = useRouter();
  const { user, setUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [cropImage, setCropImage] = useState<string | null>(null);
  const [cropType, setCropType] = useState<'avatar' | 'banner' | null>(null);
  const [formData, setFormData] = useState({
    display_name: '',
    full_name: '',
    bio: '',
    location: '',
    website_url: '',
    twitter_handle: '',
    github_username: '',
    linkedin_url: '',
    profile_public: true,
    show_email: false,
    show_real_name: false,
  });

  useEffect(() => {
    if (!user) {
      router.push('/auth/signin');
      return;
    }

    // Load current user data
    loadUserData();
  }, [user]);

  const loadUserData = async () => {
    try {
      const data = await api.getCurrentUser();
      setFormData({
        display_name: data.display_name || '',
        full_name: data.full_name || '',
        bio: data.bio || '',
        location: data.location || '',
        website_url: data.website_url || '',
        twitter_handle: data.twitter_handle || '',
        github_username: data.github_username || '',
        linkedin_url: data.linkedin_url || '',
        profile_public: data.profile_public ?? true,
        show_email: data.show_email ?? false,
        show_real_name: data.show_real_name ?? false,
      });
    } catch (error) {
      toast.error('Failed to load profile data');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const updatedUser = await api.updateProfile(formData);
      setUser(updatedUser);
      toast.success('Profile updated successfully!');
      router.push(`/@${updatedUser.display_name}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
      e.target.value = ''; // Reset input
      return;
    }

    // Create preview URL for cropper
    const reader = new FileReader();
    reader.onload = () => {
      setCropImage(reader.result as string);
      setCropType('avatar');
    };
    reader.readAsDataURL(file);
    e.target.value = ''; // Reset input
  };

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      toast.error('Banner image must be less than 10MB');
      e.target.value = ''; // Reset input
      return;
    }

    // Create preview URL for cropper
    const reader = new FileReader();
    reader.onload = () => {
      setCropImage(reader.result as string);
      setCropType('banner');
    };
    reader.readAsDataURL(file);
    e.target.value = ''; // Reset input
  };

  const handleCropComplete = async (croppedBlob: Blob) => {
    try {
      // Convert blob to file
      const file = new File([croppedBlob], 'cropped-image.jpg', { type: 'image/jpeg' });

      if (cropType === 'avatar') {
        await api.uploadProfileImage(file);
        toast.success('Avatar uploaded successfully!');
      } else if (cropType === 'banner') {
        await api.uploadBannerImage(file);
        toast.success('Banner uploaded successfully!');
      }

      // Reload current user to get new image URL
      const updatedUser = await api.getCurrentUser();
      setUser(updatedUser);
      await loadUserData();

      // Close cropper
      setCropImage(null);
      setCropType(null);
    } catch (error) {
      toast.error(`Failed to upload ${cropType === 'avatar' ? 'avatar' : 'banner'}`);
    }
  };

  const handleCropCancel = () => {
    setCropImage(null);
    setCropType(null);
  };

  if (!user) {
    return null;
  }

  return (
    <div className="py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-sage-100">Profile Settings</h1>
          <p className="text-sage-400 mt-2">Update your profile information and preferences</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Banner Upload */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold text-sage-100 mb-4">Profile Banner</h2>
            <div className="space-y-4">
              <div className="w-full h-48 rounded-lg bg-gradient-to-br from-sage-700 via-sage-600 to-charcoal-200 overflow-hidden">
                {user.banner_url ? (
                  <img src={user.banner_url} alt="Banner" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <p className="text-cream-100 text-lg font-medium">No banner image</p>
                  </div>
                )}
              </div>
              <div>
                <label htmlFor="banner-upload" className="btn-secondary cursor-pointer inline-flex items-center gap-2">
                  <Upload className="w-4 h-4" />
                  Upload Banner Image
                </label>
                <input
                  id="banner-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleBannerUpload}
                  className="hidden"
                />
                <p className="text-sm text-sage-500 mt-2">JPG or PNG. Max size 10MB. Recommended: 1500x500px</p>
              </div>
            </div>
          </div>

          {/* Avatar Upload */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold text-sage-100 mb-4">Profile Picture</h2>
            <div className="flex items-center gap-6">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-sage-500 to-sage-700 flex items-center justify-center overflow-hidden shadow-lg shadow-sage-600/40">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-3xl font-bold text-cream-100">
                    {user.display_name?.[0]?.toUpperCase() || 'U'}
                  </span>
                )}
              </div>
              <div>
                <label htmlFor="avatar-upload" className="btn-secondary cursor-pointer inline-flex items-center gap-2">
                  <Upload className="w-4 h-4" />
                  Upload New Picture
                </label>
                <input
                  id="avatar-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarUpload}
                  className="hidden"
                />
                <p className="text-sm text-sage-500 mt-2">JPG, PNG or GIF. Max size 5MB.</p>
              </div>
            </div>
          </div>

          {/* Basic Information */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold text-sage-100 mb-4">Basic Information</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="display_name" className="block text-sm font-medium text-sage-300 mb-2">
                  Display Name *
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-sage-500" />
                  <input
                    id="display_name"
                    type="text"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    className="input-primary pl-10"
                    required
                  />
                </div>
                <p className="text-xs text-sage-500 mt-1">This is your public display name</p>
              </div>

              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-sage-300 mb-2">
                  Full Name
                </label>
                <input
                  id="full_name"
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="input-primary"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label htmlFor="bio" className="block text-sm font-medium text-sage-300 mb-2">
                  Bio
                </label>
                <div className="relative">
                  <FileText className="absolute left-3 top-3 w-5 h-5 text-sage-500" />
                  <textarea
                    id="bio"
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    className="input-primary pl-10 min-h-[100px]"
                    placeholder="Tell us about yourself..."
                    maxLength={500}
                  />
                </div>
                <p className="text-xs text-sage-500 mt-1">
                  {formData.bio.length}/500 characters
                </p>
              </div>

              <div>
                <label htmlFor="location" className="block text-sm font-medium text-sage-300 mb-2">
                  Location
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-sage-500" />
                  <input
                    id="location"
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="input-primary pl-10"
                    placeholder="Calgary, AB"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Social Links */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold text-sage-100 mb-4">Social Links</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="website_url" className="block text-sm font-medium text-sage-300 mb-2">
                  Website
                </label>
                <div className="relative">
                  <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-sage-500" />
                  <input
                    id="website_url"
                    type="url"
                    value={formData.website_url}
                    onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                    className="input-primary pl-10"
                    placeholder="https://yourwebsite.com"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="twitter_handle" className="block text-sm font-medium text-sage-300 mb-2">
                  Twitter Handle
                </label>
                <div className="relative">
                  <Twitter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-sage-500" />
                  <input
                    id="twitter_handle"
                    type="text"
                    value={formData.twitter_handle}
                    onChange={(e) => setFormData({ ...formData, twitter_handle: e.target.value.replace('@', '') })}
                    className="input-primary pl-10"
                    placeholder="username"
                  />
                </div>
                <p className="text-xs text-sage-500 mt-1">Without the @ symbol</p>
              </div>

              <div>
                <label htmlFor="github_username" className="block text-sm font-medium text-sage-300 mb-2">
                  GitHub Username
                </label>
                <div className="relative">
                  <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-sage-500" />
                  <input
                    id="github_username"
                    type="text"
                    value={formData.github_username}
                    onChange={(e) => setFormData({ ...formData, github_username: e.target.value })}
                    className="input-primary pl-10"
                    placeholder="username"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="linkedin_url" className="block text-sm font-medium text-sage-300 mb-2">
                  LinkedIn Profile URL
                </label>
                <div className="relative">
                  <Linkedin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-sage-500" />
                  <input
                    id="linkedin_url"
                    type="url"
                    value={formData.linkedin_url}
                    onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                    className="input-primary pl-10"
                    placeholder="https://linkedin.com/in/username"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Privacy Settings */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold text-sage-100 mb-4">Privacy Settings</h2>
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.profile_public}
                  onChange={(e) => setFormData({ ...formData, profile_public: e.target.checked })}
                  className="w-5 h-5 rounded border-sage-700 bg-charcoal-300 text-sage-500 focus:ring-sage-500"
                />
                <div>
                  <div className="text-sage-200 font-medium">Public Profile</div>
                  <div className="text-sm text-sage-400">Allow others to view your profile</div>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.show_email}
                  onChange={(e) => setFormData({ ...formData, show_email: e.target.checked })}
                  className="w-5 h-5 rounded border-sage-700 bg-charcoal-300 text-sage-500 focus:ring-sage-500"
                />
                <div>
                  <div className="text-sage-200 font-medium">Show Email</div>
                  <div className="text-sm text-sage-400">Display your email on your public profile</div>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.show_real_name}
                  onChange={(e) => setFormData({ ...formData, show_real_name: e.target.checked })}
                  className="w-5 h-5 rounded border-sage-700 bg-charcoal-300 text-sage-500 focus:ring-sage-500"
                />
                <div>
                  <div className="text-sage-200 font-medium">Show Real Name</div>
                  <div className="text-sm text-sage-400">Display your full name on your public profile</div>
                </div>
              </label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-4">
            <button
              type="button"
              onClick={() => router.push(`/@${user.display_name}`)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
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

      {/* Image Crop Modal */}
      {cropImage && cropType && (
        <ImageCropModal
          image={cropImage}
          onCropComplete={handleCropComplete}
          onCancel={handleCropCancel}
          aspectRatio={cropType === 'avatar' ? 1 : 3}
          title={cropType === 'avatar' ? 'Crop Profile Picture' : 'Crop Banner Image'}
        />
      )}
    </div>
  );
}
