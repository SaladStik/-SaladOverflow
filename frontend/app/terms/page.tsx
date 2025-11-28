import Link from 'next/link';
import { FileText, AlertCircle, Scale, Ban, Heart } from 'lucide-react';

export const metadata = {
  title: 'Terms of Service - SaladOverflow',
  description: 'The rules of the road (aka: please be cool to each other)',
};

export default function TermsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <Link href="/" className="text-sage-400 hover:text-sage-300 transition-colors">
          ← Back to Home
        </Link>
      </div>

      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <FileText className="w-10 h-10 text-sage-400" />
          <h1 className="text-4xl font-bold text-sage-100">Terms of Service</h1>
        </div>

        <p className="text-sage-400 mb-8">
          Effective: Since day one | Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
        </p>

        <div className="space-y-8 text-sage-300">
          <section className="bg-sage-900/30 border border-sage-700 rounded-lg p-6">
            <p className="text-lg font-semibold text-sage-200 mb-2">
              Welcome to SaladOverflow! 🥗
            </p>
            <p>
              By using this site, you agree to these terms. Don't worry, we kept the legal jargon to a minimum. 
              This is basically the "don't be a jerk" agreement, with some extra steps.
            </p>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Heart className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">The Golden Rule</h2>
            </div>
            <p className="mb-4">
              Treat others the way you'd want to be treated. This isn't just grandma's advice—it's the law of the land here.
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Be respectful (even when you disagree)</li>
              <li>Help others learn (we're all students here)</li>
              <li>Give credit where it's due (plagiarism is not cool)</li>
              <li>Have fun! (That's literally why we built this)</li>
            </ul>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Ban className="w-6 h-6 text-red-400" />
              <h2 className="text-2xl font-semibold text-sage-100">The No-No List</h2>
            </div>
            <p className="mb-4">
              Don't do these things. Seriously. We will be sad if you do:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>No spam (nobody wants to hear about your crypto scheme)</li>
              <li>No harassment (be kind or be gone)</li>
              <li>No illegal content (we're not trying to get arrested here)</li>
              <li>No doxxing (keep personal info personal)</li>
              <li>No impersonation (be yourself, everyone else is taken)</li>
              <li>No breaking stuff on purpose (our server costs are already high enough)</li>
            </ul>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Scale className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Your Content, Your Responsibility</h2>
            </div>
            <p className="mb-4">
              When you post on SaladOverflow:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>You own your content (we're not stealing your brilliant ideas)</li>
              <li>You're responsible for what you post (choose your words wisely)</li>
              <li>You grant us the right to display it (otherwise the site wouldn't work)</li>
              <li>You can delete it anytime (except if we cached it, then it might take a minute)</li>
            </ul>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-6 h-6 text-yellow-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Disclaimers (The Boring But Important Part)</h2>
            </div>
            <p className="mb-4">
              Let's be real for a second:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>This is a student project (we're learning as we go)</li>
              <li>Things might break sometimes (we'll fix them, promise)</li>
              <li>Take technical advice with a grain of salt (always verify before running random code)</li>
              <li>We're not liable if you fail your assignment (but we hope we helped!)</li>
              <li>The site is provided "as is" (fancy legal term for "no guarantees")</li>
            </ul>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Changes to These Terms</h2>
            </div>
            <p>
              We might update these terms as we learn more about running a website. Major changes will be announced, 
              but it's a good idea to check back every now and then. Or don't. We're not your mom.
            </p>
          </section>

          <section className="border-t border-sage-700 pt-6">
            <h2 className="text-2xl font-semibold text-sage-100 mb-3">Still Have Questions?</h2>
            <p className="mb-4">
              If something isn't clear, or you just want to say hi, <Link href="/contact" className="text-sage-400 hover:text-sage-300 underline">reach out to us</Link>. 
              We love feedback!
            </p>
            <p className="text-sm text-sage-400 italic">
              Remember: This is a learning project for a class. If you found a bug or have suggestions, 
              we actually <span className="font-semibold">want</span> to hear about it. That's how we get better grades. 😄
            </p>
          </section>

          <section className="bg-sage-900/30 border border-sage-700 rounded-lg p-6 mt-8">
            <p className="text-center text-sage-300">
              By using SaladOverflow, you acknowledge that you've read these terms and agree to play nice. 
              Now go forth and share some knowledge!
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
