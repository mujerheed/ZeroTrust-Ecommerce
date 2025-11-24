import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ShieldCheck, Lock, FileText, Users, ArrowRight, LayoutDashboard } from "lucide-react"
import { ModeToggle } from "@/components/mode-toggle"

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <header className="px-6 h-16 flex items-center justify-between border-b border-border sticky top-0 bg-background/80 backdrop-blur-md z-50">
        <div className="flex items-center gap-2 font-bold text-xl text-primary">
          <ShieldCheck className="h-6 w-6" />
          <span>TrustGuard</span>
        </div>
        <div className="flex gap-4 items-center">
          <ModeToggle />
          <Link href="/vendor/login">
            <Button variant="ghost">Vendor Login</Button>
          </Link>
          <Link href="/ceo/login">
            <Button>CEO Login</Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="py-20 px-6 text-center space-y-6 max-w-4xl mx-auto">
          <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100">
            New: Zero Trust Architecture
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
            Secure Commerce for the <span className="text-blue-600 dark:text-blue-500">Informal Economy</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Eliminate payment fraud and build trust between vendors and buyers with our sessionless, audit-logged verification platform.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link href="/ceo/signup">
              <Button size="lg" className="h-12 px-8 text-lg shadow-lg shadow-blue-500/20">
                Register Business <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/vendor/login">
              <Button size="lg" variant="outline" className="h-12 px-8 text-lg">
                Vendor Login
              </Button>
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-slate-50 dark:bg-slate-900">
          <div className="px-6 max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12 text-slate-900 dark:text-slate-50">Why TrustGuard?</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-shadow">
                <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mb-4">
                  <Lock className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Zero Trust Security</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Every transaction is verified. Sessionless OTP authentication ensures only authorized access at every step.
                </p>
              </div>
              <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-shadow">
                <div className="h-12 w-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Receipt Verification</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Stop fake transfers. Uploaded receipts are securely stored and verified before orders are processed.
                </p>
              </div>
              <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-shadow">
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mb-4">
                  <LayoutDashboard className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">CEO Oversight</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Full visibility for business owners. Approve high-value transactions and manage vendor access centrally.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Role Selection Section */}
        <section className="py-20 px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-12">Choose Your Portal</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <Link href="/vendor/login" className="group">
                <div className="h-full p-8 rounded-2xl border-2 border-slate-200 dark:border-slate-800 hover:border-blue-500 dark:hover:border-blue-500 transition-all hover:shadow-xl bg-white dark:bg-slate-950 text-left relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Users className="h-24 w-24 text-blue-600" />
                  </div>
                  <Users className="h-10 w-10 text-blue-600 mb-4" />
                  <h3 className="text-2xl font-bold mb-2 group-hover:text-blue-600 transition-colors">Vendor Portal</h3>
                  <p className="text-slate-600 dark:text-slate-400 mb-6">
                    For sales staff managing orders, chatting with customers, and verifying payments.
                  </p>
                  <span className="text-blue-600 font-medium flex items-center group-hover:translate-x-1 transition-transform">
                    Login as Vendor <ArrowRight className="ml-2 h-4 w-4" />
                  </span>
                </div>
              </Link>

              <Link href="/ceo/login" className="group">
                <div className="h-full p-8 rounded-2xl border-2 border-slate-200 dark:border-slate-800 hover:border-purple-500 dark:hover:border-purple-500 transition-all hover:shadow-xl bg-white dark:bg-slate-950 text-left relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                    <ShieldCheck className="h-24 w-24 text-purple-600" />
                  </div>
                  <ShieldCheck className="h-10 w-10 text-purple-600 mb-4" />
                  <h3 className="text-2xl font-bold mb-2 group-hover:text-purple-600 transition-colors">CEO Portal</h3>
                  <p className="text-slate-600 dark:text-slate-400 mb-6">
                    For business owners to monitor performance, audit logs, and approve escalations.
                  </p>
                  <span className="text-purple-600 font-medium flex items-center group-hover:translate-x-1 transition-transform">
                    Login as CEO <ArrowRight className="ml-2 h-4 w-4" />
                  </span>
                </div>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-8 border-t border-slate-200 dark:border-slate-800 text-center text-slate-500 text-sm bg-slate-50 dark:bg-slate-950">
        <p>&copy; 2025 TrustGuard. All rights reserved.</p>
      </footer>
    </div>
  )
}
