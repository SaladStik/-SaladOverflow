// API and static file configuration
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

// Static file URLs
export const LOGO_URL = `${API_URL}/static/img/logo.png`;
export const STATIC_URL = `${API_URL}/static`;
