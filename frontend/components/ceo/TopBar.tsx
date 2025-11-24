"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearToken } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Bell,
  User,
  LogOut,
  Building2,
  Moon,
  Sun,
  Clock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { EscalationModal } from "./EscalationModal";
import { getSessionInfo, formatSessionTime, clearSession } from "@/lib/session";

interface TopBarProps {
  className?: string;
}

interface Notification {
  id: string;
  type: "escalation" | "alert" | "info";
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
  order_id?: string;
  vendor_id?: string;
  metadata?: {
    reason?: string;
    amount?: number;
    escalation_id?: string;
  };
}

export function TopBar({ className }: TopBarProps) {
  const router = useRouter();
  const [ceoName, setCeoName] = useState("CEO");
  const [companyName, setCompanyName] = useState("");
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [escalationModal, setEscalationModal] = useState<Notification | null>(null);
  const [lastNotificationId, setLastNotificationId] = useState<string | null>(null);
  const [sessionTime, setSessionTime] = useState<string>("60:00");
  const [isSessionWarning, setIsSessionWarning] = useState(false);

  // Update session timer every second
  useEffect(() => {
    const interval = setInterval(() => {
      const sessionInfo = getSessionInfo('ceo');
      
      if (sessionInfo.isExpired) {
        clearSession('ceo');
        clearToken();
        router.push("/ceo/login?expired=true");
        return;
      }

      setSessionTime(formatSessionTime(sessionInfo.remainingTime));
      setIsSessionWarning(sessionInfo.isWarning);
    }, 1000);

    return () => clearInterval(interval);
  }, [router]);

  useEffect(() => {
    fetchProfile();
    fetchNotifications();
    
    // Poll for notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get("/ceo/profile");
      const profile = response.data.data.ceo;
      setCeoName(profile.name);
      setCompanyName(profile.company_name || "Your Business");
    } catch (error) {
      console.error("Failed to fetch profile:", error);
    }
  };

  const fetchNotifications = async () => {
    try {
      // This endpoint would need to be implemented in backend
      const response = await api.get("/ceo/notifications");
      const fetchedNotifications = response.data.data.notifications || [];
      setNotifications(fetchedNotifications);
      
      // Check for new escalations that need to auto-pop
      if (fetchedNotifications.length > 0) {
        const latestNotif = fetchedNotifications[0];
        
        // Auto-pop if it's a new escalation (different from last seen)
        if (
          latestNotif.type === "escalation" &&
          !latestNotif.read &&
          latestNotif.id !== lastNotificationId
        ) {
          setLastNotificationId(latestNotif.id);
          setEscalationModal(latestNotif);
          
          // Play notification sound (optional)
          toast.error("New escalation requires your attention!", {
            duration: 5000,
          });
        }
      }
    } catch (error) {
      // Silent fail - notifications are not critical
      console.debug("Notifications not available");
    }
  };

  const handleLogout = () => {
    clearSession('ceo');
    clearToken('ceo');
    router.push("/");
  };

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    document.documentElement.classList.toggle("dark");
    localStorage.setItem("theme", newTheme);
  };

  const handleViewEscalation = (orderId: string) => {
    router.push(`/ceo/approvals`);
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await api.post(`/ceo/notifications/${notificationId}/read`);
      // Update local state
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        )
      );
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className={cn("h-16 border-b bg-white dark:bg-slate-900 dark:border-slate-800", className)}>
      <div className="flex items-center justify-between h-full px-6">
        {/* Left: Page Title or Search */}
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            CEO Portal
          </h2>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-4">
          {/* Session Timer */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm ${
            isSessionWarning 
              ? "bg-yellow-500/10 text-yellow-600 dark:text-yellow-500 border border-yellow-500/20" 
              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
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
            className="relative text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
          >
            {theme === "light" ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </Button>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
                <Bell className="h-5 w-5" />
                {unreadCount > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                  >
                    {unreadCount}
                  </Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              <DropdownMenuLabel>Notifications</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {notifications.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  No new notifications
                </div>
              ) : (
                <div className="max-h-96 overflow-y-auto">
                  {notifications.slice(0, 5).map((notification) => (
                    <DropdownMenuItem
                      key={notification.id}
                      className="flex flex-col items-start p-3 cursor-pointer"
                      onClick={() => {
                        // Mark as read
                        if (!notification.read) {
                          handleMarkAsRead(notification.id);
                        }
                        // Navigate to approvals page
                        if (notification.order_id) {
                          router.push(`/ceo/approvals`);
                        }
                      }}
                    >
                      <div className="flex items-start justify-between w-full">
                        <span className="font-medium text-sm">
                          {notification.title}
                        </span>
                        {!notification.read && (
                          <div className="h-2 w-2 bg-blue-600 rounded-full" />
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {notification.message}
                      </p>
                      <span className="text-xs text-muted-foreground mt-1">
                        {new Date(notification.timestamp * 1000).toLocaleString()}
                      </span>
                    </DropdownMenuItem>
                  ))}
                </div>
              )}
              {notifications.length > 0 && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    className="justify-center text-blue-600 dark:text-blue-400 cursor-pointer"
                    onClick={async () => {
                      // Mark all as read
                      try {
                        await api.post('/ceo/notifications/read-all');
                        setNotifications((prev) =>
                          prev.map((n) => ({ ...n, read: true }))
                        );
                        toast.success('All notifications marked as read');
                      } catch (error) {
                        console.error('Failed to mark all as read:', error);
                      }
                    }}
                  >
                    Mark all as read
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Profile Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
                <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                  <User className="h-4 w-4 text-white" />
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">{ceoName}</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{companyName}</p>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">{ceoName}</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400 font-normal">
                    {companyName}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/ceo/settings")}>
                <User className="h-4 w-4 mr-2 text-slate-700 dark:text-slate-300" />
                <span className="text-slate-900 dark:text-white">Profile Settings</span>
              </DropdownMenuItem>
              <DropdownMenuItem disabled>
                <Building2 className="h-4 w-4 mr-2 text-slate-700 dark:text-slate-300" />
                <span className="text-slate-900 dark:text-white">Switch Business</span>
                <Badge variant="secondary" className="ml-auto text-xs">
                  Soon
                </Badge>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-red-600 dark:text-red-400 focus:text-red-600 dark:focus:text-red-400"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Escalation Auto-Pop Modal */}
      <EscalationModal
        escalation={
          escalationModal
            ? {
                id: escalationModal.id,
                order_id: escalationModal.order_id || "",
                vendor_id: escalationModal.vendor_id,
                amount: escalationModal.metadata?.amount,
                reason: escalationModal.metadata?.reason,
                title: escalationModal.title,
                message: escalationModal.message,
              }
            : null
        }
        onClose={() => setEscalationModal(null)}
        onViewDetails={handleViewEscalation}
      />
    </div>
  );
}
