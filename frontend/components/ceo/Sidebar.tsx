"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  ShoppingCart,
  AlertTriangle,
  Shield,
  Settings,
  Plug,
  BarChart3,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface SidebarProps {
  className?: string;
}

const menuItems = [
  {
    title: "Dashboard",
    href: "/ceo/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Vendors",
    href: "/ceo/vendors",
    icon: Users,
  },
  {
    title: "Orders",
    href: "/ceo/orders",
    icon: ShoppingCart,
  },
  {
    title: "Approvals",
    href: "/ceo/approvals",
    icon: AlertTriangle,
  },
  {
    title: "Analytics",
    href: "/ceo/analytics",
    icon: BarChart3,
  },
  {
    title: "Audit Logs",
    href: "/ceo/audit-logs",
    icon: Shield,
  },
  {
    title: "Integrations",
    href: "/ceo/integrations",
    icon: Plug,
  },
  {
    title: "Settings",
    href: "/ceo/settings",
    icon: Settings,
  },
];

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={cn(
        "relative flex flex-col h-screen bg-slate-900 text-white transition-all duration-300",
        collapsed ? "w-16" : "w-64",
        className
      )}
    >
      {/* Logo Section */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-500" />
            <span className="font-bold text-lg">TrustGuard</span>
          </div>
        )}
        {collapsed && <Shield className="h-6 w-6 text-blue-500 mx-auto" />}
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <li key={item.href}>
                <Link href={item.href}>
                  <div
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                      isActive
                        ? "bg-blue-600 text-white"
                        : "text-slate-300 hover:bg-slate-800 hover:text-white"
                    )}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {!collapsed && (
                      <span className="font-medium">{item.title}</span>
                    )}
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Collapse Toggle */}
      <div className="p-4 border-t border-slate-800">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="w-full text-slate-300 hover:text-white hover:bg-slate-800"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <>
              <ChevronLeft className="h-5 w-5 mr-2" />
              Collapse
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
