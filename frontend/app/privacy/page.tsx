import Link from 'next/link';
import { Shield, Eye, Lock, Cookie, Server, UserX } from 'lucide-react';

export const metadata = {
  title: 'Privacy Policy - SaladOverflow',
  description: 'How we protect your data (spoiler: we take it very seriously)',
};

export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <Link href="/" className="text-sage-400 hover:text-sage-300 transition-colors">
          ← Back to Home
        </Link>
      </div>

      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="w-10 h-10 text-sage-400" />
          <h1 className="text-4xl font-bold text-sage-100">Privacy Policy</h1>
        </div>

        <p className="text-sage-400 mb-8">
          Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
        </p>

        <div className="space-y-8 text-sage-300">
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Eye className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">What We Collect</h2>
            </div>
            <p className="mb-4">
              We collect the bare minimum to keep SaladOverflow running smoothly:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Your email (so you can reset your password when you inevitably forget it)</li>
              <li>Your username (because "Anonymous User #47382" isn't very catchy)</li>
              <li>Your posts and comments (that's... kind of the whole point)</li>
              <li>Cookies (the digital kind, not the delicious kind 🍪)</li>
            </ul>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Lock className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">How We Protect Your Data</h2>
            </div>
            <p className="mb-4">
              Your data security is our top priority:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Passwords are hashed with bcrypt (even we can't see them!)</li>
              <li>HTTPS everywhere (because plain HTTP is so 1995)</li>
              <li>Secure session tokens (no sticky notes with passwords here)</li>
              <li>Regular security updates (we actually read those CVE reports)</li>
            </ul>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Cookie className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Cookies Policy</h2>
            </div>
            <p className="mb-4">
              We use cookies to remember you're logged in. That's it. No tracking, no ads, no selling your data to the highest bidder.
            </p>
            <p className="text-sm text-sage-400 italic">
              If you disable cookies, you'll have to log in every time.
            </p>
          </section>

        <section>
            <div className="flex items-center gap-2 mb-3">
                <Server className="w-6 h-6 text-sage-400" />
                <h2 className="text-2xl font-semibold text-sage-100">Data Storage</h2>
            </div>
            <p className="mb-4">
                Your data is stored in my living room console on my homelab, and is not being backed up because I don't value your data.
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Physically hosted on my home hardware (no enterprise guarantees)</li>
            </ul>
        </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <UserX className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Your Rights</h2>
            </div>
            <p className="mb-4">
              You have the right to:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Access your data (just log in, it's all there)</li>
              <li>Update your information (change is good!)</li>
            </ul>
          </section>

          <section className="border-t border-sage-700 pt-6">
            <h2 className="text-2xl font-semibold text-sage-100 mb-3">Questions?</h2>
            <p>
              If you have any questions about our privacy policy, or just want to chat about data protection over coffee, 
              feel free to <a href="mailto:nick@saladsync.ca" className="text-sage-400 hover:text-sage-300 underline">reach out to us</a>.
            </p>
            <p className="text-sm text-sage-400 italic mt-4">
              P.S. - This is a student project. We're learning as we go, so please be gentle with feedback.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
