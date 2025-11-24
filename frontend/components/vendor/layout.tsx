"use client"

import { useEffect, useState, useRef } from "react"
import { VendorSidebar } from "@/components/vendor/sidebar-new"
import { VendorTopbar } from "@/components/vendor/topbar"
import { PreferencesModal } from "@/components/vendor/preferences-modal"
import { api } from "@/lib/api"
import { toast } from "sonner"
import { useRouter } from "next/navigation"

interface VendorLayoutProps {
  children: React.ReactNode
}

interface NotificationEvent {
  type: "new_order" | "receipt_uploaded" | "order_flagged" | "high_value_alert"
  order_id: string
  buyer_id?: string
  amount?: number
  timestamp: number
}

export function VendorLayout({ children }: VendorLayoutProps) {
  const router = useRouter()
  const [pendingReceipts, setPendingReceipts] = useState(0)
  const [unreadMessages, setUnreadMessages] = useState(0)
  const [vendorName, setVendorName] = useState("Vendor")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const lastNotificationCheck = useRef<number>(Date.now())

  useEffect(() => {
    fetchNotifications()
    fetchVendorInfo()
    
    // Poll for notifications every 15 seconds for real-time alerts
    const interval = setInterval(checkForNewEvents, 15000)
    return () => clearInterval(interval)
  }, [])

  async function fetchVendorInfo() {
    try {
      const response = await api.get("/vendor/dashboard")
      const vendor = response.data.data.vendor_info
      setVendorName(vendor?.name || "Vendor")
    } catch (error) {
      console.error("Failed to fetch vendor info:", error)
    }
  }

  async function fetchNotifications() {
    try {
      const response = await api.get("/vendor/notifications/unread")
      const data = response.data.data
      
      // Extract counts from notifications
      setPendingReceipts(data.new_count || 0)
      setUnreadMessages(0) // TODO: Add unread messages count when backend supports it
    } catch (error) {
      console.error("Failed to fetch notifications:", error)
    }
  }

  async function checkForNewEvents() {
    try {
      const response = await api.get("/vendor/notifications/recent", {
        params: {
          since: Math.floor(lastNotificationCheck.current / 1000)
        }
      })
      
      const events: NotificationEvent[] = response.data.data.events || []
      
      // Show toast for each new event
      events.forEach((event) => {
        showEventToast(event)
      })

      // Update last check timestamp
      lastNotificationCheck.current = Date.now()
      
      // Refresh counts
      await fetchNotifications()
    } catch (error) {
      // Silent fail for polling - don't spam user with errors
      console.debug("Notification polling failed:", error)
    }
  }

  function showEventToast(event: NotificationEvent) {
    const maskedBuyerId = event.buyer_id 
      ? `+234***${event.buyer_id.slice(-4)}` 
      : "buyer"

    switch (event.type) {
      case "new_order":
        toast.success(
          `New order from ${maskedBuyerId}`,
          {
            description: `Order #${event.order_id.slice(-8)}`,
            action: {
              label: "View",
              onClick: () => router.push(`/vendor/orders`)
            },
            duration: 8000,
          }
        )
        break

      case "receipt_uploaded":
        toast.info(
          `Receipt uploaded for Order #${event.order_id.slice(-8)}`,
          {
            description: `Amount: ₦${((event.amount || 0) / 100).toLocaleString()}`,
            action: {
              label: "Verify",
              onClick: () => router.push(`/vendor/receipts`)
            },
            duration: 10000,
          }
        )
        break

      case "order_flagged":
        toast.warning(
          `⚠️ Order flagged for review`,
          {
            description: `Order #${event.order_id.slice(-8)} requires attention`,
            action: {
              label: "Review",
              onClick: () => router.push(`/vendor/receipts`)
            },
            duration: 15000,
          }
        )
        break

      case "high_value_alert":
        toast.error(
          `🚨 High-value transaction alert`,
          {
            description: `₦${((event.amount || 0) / 100).toLocaleString()} - CEO approval required`,
            action: {
              label: "View",
              onClick: () => router.push(`/vendor/orders`)
            },
            duration: 20000,
          }
        )
        break
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className={sidebarCollapsed ? "w-20" : "w-64"} style={{ transition: "width 0.3s" }}>
        <VendorSidebar 
          pendingReceipts={pendingReceipts}
          unreadMessages={unreadMessages}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <VendorTopbar 
          vendorName={vendorName}
          notificationCount={pendingReceipts}
        />
        
        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Floating Preferences Button */}
      <PreferencesModal />
    </div>
  )
}
