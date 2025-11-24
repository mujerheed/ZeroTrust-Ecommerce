"use client"

import { motion } from "framer-motion"
import { ShieldCheck } from "lucide-react"
import Link from "next/link"
import { ModeToggle } from "@/components/mode-toggle"

interface AuthWrapperProps {
  children: React.ReactNode
  title: string
  description: string
  backButton?: {
    label: string
    href?: string
    onClick?: () => void
  }
}

export function AuthWrapper({ children, title, description, backButton }: AuthWrapperProps) {
  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100 dark:from-slate-950 dark:via-slate-900 dark:to-blue-950">
      {/* Background Elements */}
      <div className="absolute inset-0 w-full h-full pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-400/20 blur-[100px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-400/20 blur-[100px]" />
      </div>

      <div className="absolute top-4 right-4 z-50">
        <ModeToggle />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md z-10 px-4"
      >
        <div className="mb-8 text-center flex flex-col items-center">
          <Link href="/" className="inline-flex items-center gap-2 text-2xl font-bold text-primary mb-2 hover:opacity-80 transition-opacity">
            <div className="p-2 rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-800 dark:from-blue-400 dark:to-blue-200">
              TrustGuard
            </span>
          </Link>
          <h1 className="text-2xl font-bold tracking-tight mt-4">{title}</h1>
          <p className="text-muted-foreground mt-2 text-sm">{description}</p>
        </div>

        <div className="bg-card/80 backdrop-blur-xl border border-border/50 shadow-2xl rounded-2xl p-6 md:p-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent dark:from-white/5 dark:to-transparent pointer-events-none" />
          <div className="relative z-10">
            {children}
          </div>
        </div>

        {backButton && (
          <div className="mt-6 text-center">
            {backButton.onClick ? (
              <button
                onClick={backButton.onClick}
                className="text-sm text-muted-foreground hover:text-primary transition-colors font-medium bg-transparent border-none cursor-pointer"
              >
                {backButton.label}
              </button>
            ) : (
              <Link 
                href={backButton.href || "#"}
                className="text-sm text-muted-foreground hover:text-primary transition-colors font-medium"
              >
                {backButton.label}
              </Link>
            )}
          </div>
        )}
      </motion.div>
    </div>
  )
}
