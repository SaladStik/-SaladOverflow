# SaladOverflow Frontend

Modern Q&A platform frontend built with Next.js 14, TypeScript, and Tailwind CSS.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **API Client**: Axios
- **Icons**: Lucide React
- **Markdown**: React Markdown with syntax highlighting
- **Notifications**: React Hot Toast

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local and set your API URL
```

### Development

```bash
# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
# Create production build
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                 # Next.js app router pages
│   ├── auth/            # Authentication pages (signin, signup)
│   ├── feed/            # Main feed page
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Home page (redirects to feed)
├── lib/                 # Utilities and configuration
│   ├── api.ts           # API client with Axios
│   ├── store.ts         # Zustand state management
│   └── utils.ts         # Helper functions
├── components/          # Reusable React components
└── public/              # Static assets
```

## Features

- ✅ User authentication (signin/signup)
- ✅ Post feed with infinite scroll
- ✅ Markdown rendering with syntax highlighting
- ✅ Voting system (upvote/downvote)
- ✅ Bookmarking
- ✅ Tag system
- ✅ User profiles
- ✅ Responsive design
- ✅ Dark theme

## API Integration

The frontend connects to the SaladOverflow API at the URL specified in `.env.local`.

Default API endpoint: `http://localhost:8000/api`

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (required)

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Create production build
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## License

MIT
