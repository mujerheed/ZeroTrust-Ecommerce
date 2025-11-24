"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Bell, Moon, Sun, LogOut, User, Clock } from "lucide-react"
import { clearToken, api } from "@/lib/api"
import { useTheme } from "next-themes"
import { getSessionInfo, formatSessionTime, clearSession } from "@/lib/session"

interface VendorTopbarProps {
  vendorName?: string
  notificationCount?: number
}

export function VendorTopbar({ vendorName = "Vendor", notificationCount = 0 }: VendorTopbarProps) {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [sessionTime, setSessionTime] = useState<string>("60:00")
  const [isSessionWarning, setIsSessionWarning] = useState(false)

  // Update session timer every second
  useEffect(() => {
    const interval = setInterval(() => {
      const sessionInfo = getSessionInfo('vendor')
      
      if (sessionInfo.isExpired) {
        clearSession('vendor')
        clearToken()
        router.push("/vendor/login?expired=true")
        return
      }

      setSessionTime(formatSessionTime(sessionInfo.remainingTime))
      setIsSessionWarning(sessionInfo.isWarning)
    }, 1000)

    return () => clearInterval(interval)
  }, [router])

  useEffect(() => {
    setMounted(true)
  }, [])

  function handleLogout() {
    clearSession('vendor')
    clearToken('vendor')
    router.push("/")
  }

  function toggleTheme() {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  return (
    <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center px-6 gap-4">
        {/* Left side - could add breadcrumbs or page title here */}
        <div className="flex-1">
          {/* Empty for now, can add breadcrumbs later */}
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          {/* Session Timer */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm ${
            isSessionWarning 
              ? "bg-yellow-500/10 text-yellow-600 dark:text-yellow-500 border border-yellow-500/20" 
              : "bg-muted text-muted-foreground"
          }`}>
            <Clock className="h-4 w-4" />
            <span className="font-mono">{sessionTime}</span>
            {isSessionWarning && <span className="text-xs ml-1">remaining</span>}
          </div>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="relative"
          >
            {mounted && (
              <>
                {theme === "dark" ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </>
            )}
            <span className="sr-only">Toggle theme</span>
          </Button>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                {notificationCount > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                  >
                    {notificationCount > 9 ? "9+" : notificationCount}
                  </Badge>
                )}
                <span className="sr-only">Notifications</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              <DropdownMenuLabel>Notifications</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {notificationCount === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  No new notifications
                </div>
              ) : (
                <div className="p-2 text-sm">
                  <div className="flex items-center gap-2 p-2 hover:bg-accent rounded cursor-pointer">
                    <div className="h-2 w-2 rounded-full bg-blue-500" />
                    <div>
                      <p className="font-medium">{notificationCount} pending receipts</p>
                      <p className="text-xs text-muted-foreground">Awaiting verification</p>
                    </div>
                  </div>
                </div>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/vendor/receipts")}>
                View all notifications
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-2">
                <User className="h-5 w-5" />
                <span className="hidden md:inline">{vendorName}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/vendor/dashboard")}>
                Dashboard
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}
