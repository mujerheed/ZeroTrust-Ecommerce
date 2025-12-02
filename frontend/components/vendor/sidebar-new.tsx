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
  ChevronLeft,
  ChevronRight,
  Shield,
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
  className,
  collapsed = false,
  onToggle
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

  function isActive(href: string): boolean {
    return pathname.startsWith(href)
  }

  return (
    <div className={cn("flex flex-col h-full bg-card border-r transition-all duration-300", className)}>
      {/* Logo/Brand */}
      <div className="p-6 flex items-center justify-between">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-primary">TrustGuard</h2>
              <p className="text-sm text-muted-foreground">Vendor Portal</p>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="flex flex-col items-center gap-2">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Shield className="h-6 w-6 text-primary" />
            </div>
          </div>
        )}
        {onToggle && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className={cn("flex-shrink-0", collapsed && "mx-auto mt-2")}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        )}
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
                "w-full",
                collapsed ? "justify-center px-2" : "justify-start",
                active && "bg-primary/10 text-primary hover:bg-primary/20"
              )}
              onClick={() => router.push(item.href)}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={cn("h-5 w-5", !collapsed && "mr-3")} />
              {!collapsed && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <Badge variant="destructive" className="ml-2">
                      {item.badge}
                    </Badge>
                  )}
                </>
              )}
              {collapsed && item.badge !== undefined && item.badge > 0 && (
                <div className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-destructive flex items-center justify-center text-[10px] text-white">
                  {item.badge > 9 ? "9+" : item.badge}
                </div>
              )}
            </Button>
          )
        })}
      </nav>
    </div>
  )
}
