"use client"

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"
import { VendorLayout } from "@/components/vendor/layout"
import {
  Send,
  DollarSign,
  CreditCard,
  FileImage,
  ArrowLeft,
  MessageCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface Message {
  message_id: string
  sender: "buyer" | "vendor"
  text: string
  timestamp: number
  time_ago: string
  platform?: "whatsapp" | "instagram"
}

interface OrderDetails {
  order_id: string
  buyer_id: string
  buyer_name: string
  total_amount: number
  status: string
  platform: "whatsapp" | "instagram"
  created_at: number
}

export default function NegotiationPage() {
  const params = useParams()
  const router = useRouter()
  const order_id = params.id as string

  const [messages, setMessages] = useState<Message[]>([])
  const [orderDetails, setOrderDetails] = useState<OrderDetails | null>(null)
  const [newMessage, setNewMessage] = useState("")
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchOrderDetails()
    fetchMessages()
    
    // Poll for new messages every 10 seconds
    const interval = setInterval(fetchMessages, 10000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [order_id])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  async function fetchOrderDetails() {
    try {
      const response = await api.get(`/vendor/orders/${order_id}`)
      const order = response.data.data
      
      // Determine platform from buyer_id prefix
      const platform = order.buyer_id.startsWith("wa_") ? "whatsapp" : "instagram"
      
      setOrderDetails({
        ...order,
        platform,
      })
    } catch (error: any) {
      toast.error("Failed to load order details")
      if (error.response?.status === 401) {
        router.push("/vendor/login")
      }
    }
  }

  async function fetchMessages() {
    try {
      const response = await api.get(`/vendor/orders/${order_id}/messages?limit=50`)
      setMessages(response.data.data.messages || [])
    } catch (error: any) {
      console.error("Failed to load messages:", error)
      // Don't show error toast for polling failures
    } finally {
      setLoading(false)
    }
  }

  async function sendMessage(quick_action?: string) {
    if (!newMessage.trim() && !quick_action) return

    try {
      setSending(true)
      const response = await api.post(`/vendor/orders/${order_id}/messages`, {
        message: newMessage || undefined,
        quick_action,
      })

      toast.success("Message sent successfully")
      setNewMessage("")
      
      // Refresh messages
      await fetchMessages()
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to send message")
    } finally {
      setSending(false)
    }
  }

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  function formatTime(timestamp: number): string {
    const date = new Date(timestamp * 1000)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <VendorLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading conversation...</p>
          </div>
        </div>
      </VendorLayout>
    )
  }

  return (
    <VendorLayout>
      <div>
      {/* Header */}
      <div className="border-b bg-card sticky top-0 z-10">
        <div className="max-w-5xl mx-auto p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push("/vendor/orders")}
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold flex items-center gap-2">
                  <MessageCircle className="h-5 w-5" />
                  {orderDetails?.buyer_name || "Buyer"}
                </h1>
                <p className="text-sm text-muted-foreground">
                  Order #{order_id} • {orderDetails?.platform === "whatsapp" ? "WhatsApp" : "Instagram"}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-semibold">
                ₦{((orderDetails?.total_amount || 0) / 100).toLocaleString()}
              </p>
              <Badge variant={
                orderDetails?.status === "PENDING" ? "secondary" :
                orderDetails?.status === "APPROVED" ? "default" : "destructive"
              }>
                {orderDetails?.status}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="max-w-5xl mx-auto p-4">
        <div className="space-y-6">
          {/* Order Info Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Order Details</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Order ID</p>
                <p className="font-mono mt-1">{order_id}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Buyer</p>
                <p className="mt-1">{orderDetails?.buyer_name}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Amount</p>
                <p className="font-semibold mt-1">
                  ₦{((orderDetails?.total_amount || 0) / 100).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <Badge className="mt-1" variant={
                  orderDetails?.status === "PENDING" ? "secondary" :
                  orderDetails?.status === "APPROVED" ? "default" : "destructive"
                }>
                  {orderDetails?.status}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => sendMessage("confirm_price")}
                  disabled={sending}
                >
                  <DollarSign className="mr-2 h-4 w-4" />
                  Confirm Price
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => sendMessage("send_payment_details")}
                  disabled={sending}
                >
                  <CreditCard className="mr-2 h-4 w-4" />
                  Send Payment Details
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => sendMessage("request_receipt")}
                  disabled={sending}
                >
                  <FileImage className="mr-2 h-4 w-4" />
                  Request Receipt
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Messages */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                <span>Conversation</span>
                <span className="text-xs text-muted-foreground font-normal">
                  Messages sent via @{orderDetails?.platform === "whatsapp" ? "business WhatsApp" : "business Instagram"}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-[500px] overflow-y-auto pr-4">
                {messages.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <MessageCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No messages yet. Start the conversation!</p>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.message_id}
                      className={cn(
                        "flex",
                        message.sender === "vendor" ? "justify-end" : "justify-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[70%] rounded-lg p-3",
                          message.sender === "vendor"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        )}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                        <p
                          className={cn(
                            "text-xs mt-1",
                            message.sender === "vendor"
                              ? "text-primary-foreground/70"
                              : "text-muted-foreground"
                          )}
                        >
                          {message.time_ago || formatTime(message.timestamp)}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="mt-4 pt-4 border-t space-y-3">
                {/* Quick Actions Bar */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendMessage(`Confirmed price: ₦${((orderDetails?.total_amount || 0) / 100).toLocaleString()}`)}
                    disabled={sending}
                    className="gap-2"
                  >
                    <DollarSign className="h-4 w-4" />
                    Confirm Price: ₦{((orderDetails?.total_amount || 0) / 100).toLocaleString()}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendMessage("send_payment_details")}
                    disabled={sending}
                    className="gap-2"
                  >
                    <CreditCard className="h-4 w-4" />
                    Send Payment Details
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendMessage("request_receipt")}
                    disabled={sending}
                    className="gap-2"
                  >
                    <FileImage className="h-4 w-4" />
                    Request Receipt
                  </Button>
                </div>

                {/* Text Input */}
                <div className="flex gap-2">
                  <Textarea
                    placeholder="Type your message..."
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        sendMessage()
                      }
                    }}
                    rows={2}
                    className="resize-none"
                  />
                  <Button
                    onClick={() => sendMessage()}
                    disabled={!newMessage.trim() || sending}
                    size="icon"
                    className="h-auto"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Press Enter to send, Shift+Enter for new line
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
    </VendorLayout>
  )
}
