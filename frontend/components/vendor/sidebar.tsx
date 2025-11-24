"use client"

import { usePathname, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { clearToken } from "@/lib/api"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Package,
  FileImage,
  Users,
  MessageCircle,
  LogOut,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: number
}

interface VendorSidebarProps {
  pendingReceipts?: number
  unreadMessages?: number
  className?: string
  collapsed?: boolean
  onToggle?: () => void
}

export function VendorSidebar({ 
  pendingReceipts = 0, 
  unreadMessages = 0,
  className 
}: VendorSidebarProps) {
  const pathname = usePathname()
  const router = useRouter()

  const navItems: NavItem[] = [
    {
      label: "Dashboard",
      href: "/vendor/dashboard",
      icon: LayoutDashboard,
    },
    {
      label: "Orders",
      href: "/vendor/orders",
      icon: Package,
    },
    {
      label: "Receipts",
      href: "/vendor/receipts",
      icon: FileImage,
      badge: pendingReceipts,
    },
    {
      label: "Buyers",
      href: "/vendor/buyers",
      icon: Users,
    },
  ]

  function handleLogout() {
    clearToken()
    router.push("/")
  }

  function isActive(href: string): boolean {
    return pathname.startsWith(href)
  }

  return (
    <div className={cn("flex flex-col h-full bg-card border-r", className)}>
      {/* Logo/Brand */}
      <div className="p-6">
        <h2 className="text-2xl font-bold text-primary">TrustGuard</h2>
        <p className="text-sm text-muted-foreground">Vendor Portal</p>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = isActive(item.href)

          return (
            <Button
              key={item.href}
              variant={active ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start",
                active && "bg-primary/10 text-primary hover:bg-primary/20"
              )}
              onClick={() => router.push(item.href)}
            >
              <Icon className="mr-3 h-5 w-5" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {item.badge}
                </Badge>
              )}
            </Button>
          )
        })}
      </nav>
    </div>
  )
}
