import Link from 'next/link';
import { MessageCircle, ThumbsUp, ThumbsDown, Flag, Users, Lightbulb, Code } from 'lucide-react';

export const metadata = {
  title: 'Community Guidelines - SaladOverflow',
  description: 'How to be an awesome community member',
};

export default function GuidelinesPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <Link href="/" className="text-sage-400 hover:text-sage-300 transition-colors">
          ← Back to Home
        </Link>
      </div>

      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <Users className="w-10 h-10 text-sage-400" />
          <h1 className="text-4xl font-bold text-sage-100">Community Guidelines</h1>
        </div>

        <p className="text-sage-300 text-lg mb-8">
          Welcome to the SaladOverflow community! Here's how to make the most of your time here and help others do the same. 
          Think of this as the "how to not get kicked out" guide, but in a friendly way.
        </p>

        <div className="space-y-8 text-sage-300">
          <section className="bg-gradient-to-br from-sage-900/50 to-sage-800/30 border border-sage-600 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-sage-100 mb-3">🎯 Our Mission</h2>
            <p className="text-lg">
              To create a supportive space where students can ask questions, share knowledge, and learn from each other 
              without fear of judgment. Because let's face it, we've all Googled "how to center a div" at 2 AM.
            </p>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <MessageCircle className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Asking Good Questions</h2>
            </div>
            <p className="mb-4">
              The art of asking questions is half the battle. Here's how to get great answers:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Be specific</strong> - "My code doesn't work" vs "I'm getting a TypeError on line 42"</li>
              <li><strong>Show your work</strong> - Share what you've tried (even if it failed miserably)</li>
              <li><strong>Include context</strong> - What are you building? What's the goal?</li>
              <li><strong>Format your code</strong> - Use code blocks! We have syntax highlighting for a reason</li>
              <li><strong>Search first</strong> - Someone might have already asked your question</li>
            </ul>
            <p className="text-sm text-sage-400 italic mt-3">
              Pro tip: Explaining your problem clearly often helps you find the solution yourself. It's called rubber duck debugging!
            </p>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-6 h-6 text-yellow-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Giving Great Answers</h2>
            </div>
            <p className="mb-4">
              Helping others is awesome! Here's how to do it well:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Explain, don't just solve</strong> - Teach them to fish, don't just hand them a fish</li>
              <li><strong>Be patient</strong> - Everyone was a beginner once (yes, even you)</li>
              <li><strong>Provide resources</strong> - Links to docs, tutorials, or relevant articles</li>
              <li><strong>Test your solution</strong> - Make sure it actually works before posting</li>
              <li><strong>Be kind</strong> - There are no stupid questions, only opportunities to learn</li>
            </ul>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Code className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Code of Conduct</h2>
            </div>
            <div className="space-y-4">
              <div className="border-l-4 border-green-500 pl-4 bg-green-900/20 py-2">
                <h3 className="font-semibold text-green-400 mb-2">✅ Do This:</h3>
                <ul className="list-disc list-inside space-y-1 ml-2 text-sm">
                  <li>Respect different skill levels and learning styles</li>
                  <li>Give credit when you use someone else's code or idea</li>
                  <li>Accept feedback gracefully (even if it stings a little)</li>
                  <li>Celebrate others' successes (good vibes only!)</li>
                  <li>Ask for clarification if you don't understand</li>
                </ul>
              </div>

              <div className="border-l-4 border-red-500 pl-4 bg-red-900/20 py-2">
                <h3 className="font-semibold text-red-400 mb-2">❌ Don't Do This:</h3>
                <ul className="list-disc list-inside space-y-1 ml-2 text-sm">
                  <li>Be condescending or dismissive ("just Google it" is not helpful)</li>
                  <li>Share complete homework solutions (help them learn, don't do it for them)</li>
                  <li>Post off-topic content (this isn't Reddit... yet)</li>
                  <li>Argue in bad faith (healthy debate is good, flame wars are not)</li>
                  <li>Downvote without explaining why (anonymous negativity helps no one)</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <ThumbsUp className="w-6 h-6 text-sage-400" />
              <ThumbsDown className="w-6 h-6 text-sage-400" />
              <h2 className="text-2xl font-semibold text-sage-100">Using Votes Wisely</h2>
            </div>
            <p className="mb-4">
              Votes help surface the best content. Here's how to use them:
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-sage-900/30 border border-sage-700 rounded-lg p-4">
                <h3 className="font-semibold text-sage-200 mb-2 flex items-center gap-2">
                  <ThumbsUp className="w-5 h-5 text-green-400" />
                  Upvote when:
                </h3>
                <ul className="list-disc list-inside space-y-1 text-sm ml-2">
                  <li>The answer is helpful and accurate</li>
                  <li>The question is well-formatted and clear</li>
                  <li>Someone provides useful context or resources</li>
                  <li>A comment adds value to the discussion</li>
                </ul>
              </div>

              <div className="bg-sage-900/30 border border-sage-700 rounded-lg p-4">
                <h3 className="font-semibold text-sage-200 mb-2 flex items-center gap-2">
                  <ThumbsDown className="w-5 h-5 text-red-400" />
                  Downvote when:
                </h3>
                <ul className="list-disc list-inside space-y-1 text-sm ml-2">
                  <li>The answer is incorrect or misleading</li>
                  <li>The post lacks effort or context</li>
                  <li>Content is off-topic or spam</li>
                  <li>Someone is being rude or unhelpful</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3">
              <Flag className="w-6 h-6 text-red-400" />
              <h2 className="text-2xl font-semibold text-sage-100">When to Report Content</h2>
            </div>
            <p className="mb-4">
              See something that violates our guidelines? Let us know! Report posts that contain:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Harassment or hate speech (zero tolerance policy)</li>
              <li>Spam or self-promotion (we get it, your SaaS is cool, but no)</li>
              <li>Plagiarized content (give credit where it's due!)</li>
              <li>Personal information (doxxing is super not cool)</li>
              <li>Illegal content (we don't want to go to jail, thanks)</li>
            </ul>
          </section>

          <section className="border-t border-sage-700 pt-6">
            <h2 className="text-2xl font-semibold text-sage-100 mb-3">Remember</h2>
            <div className="bg-gradient-to-br from-sage-900/50 to-charcoal-200/30 border border-sage-600 rounded-lg p-6">
              <p className="text-lg mb-4">
                We're all here to learn and grow. Be the kind of community member you'd want to interact with.
              </p>
              <p className="text-sage-400">
                These guidelines will evolve as our community grows. Got suggestions? We'd love to hear them! 
                This is <strong>your</strong> community too.
              </p>
            </div>
          </section>

          <section className="text-center pt-6">
            <p className="text-sm text-sage-400 italic">
              P.S. - why did you read all of this.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
