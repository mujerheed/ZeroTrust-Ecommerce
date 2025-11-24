"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"
import { 
  ArrowLeft, 
  Package, 
  User, 
  Calendar, 
  DollarSign, 
  MapPin, 
  Phone, 
  Mail,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download
} from "lucide-react"
import Link from "next/link"

interface OrderDetails {
  order_id: string
  buyer_id: string
  vendor_id: string
  vendor_name?: string
  buyer_name?: string
  buyer_phone?: string
  buyer_email?: string
  total_amount: number
  order_status: string
  items?: Array<{
    item_name: string
    quantity: number
    price: number
  }>
  delivery_address?: string
  payment_method?: string
  receipt_url?: string
  notes?: string
  created_at: string
  updated_at?: string
  approved_at?: string
  approved_by?: string
}

const STATUS_CONFIG: { [key: string]: { color: string; icon: any; label: string } } = {
  pending: { color: "bg-yellow-100 text-yellow-800 border-yellow-300", icon: Clock, label: "Pending" },
  confirmed: { color: "bg-blue-100 dark:bg-blue-950/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-800", icon: CheckCircle, label: "Confirmed" },
  paid: { color: "bg-green-100 dark:bg-green-950/30 text-green-800 dark:text-green-300 border-green-300 dark:border-green-800", icon: DollarSign, label: "Paid" },
  completed: { color: "bg-green-100 dark:bg-green-950/30 text-green-800 dark:text-green-300 border-green-300 dark:border-green-800", icon: CheckCircle, label: "Completed" },
  flagged: { color: "bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-800", icon: AlertTriangle, label: "Flagged" },
  rejected: { color: "bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-800", icon: AlertTriangle, label: "Rejected" },
  cancelled: { color: "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-600", icon: AlertTriangle, label: "Cancelled" },
}

export default function OrderDetailPage() {
  const [order, setOrder] = useState<OrderDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const params = useParams()
  const orderId = params.orderId as string

  useEffect(() => {
    if (orderId) {
      fetchOrderDetails()
    }
  }, [orderId])

  async function fetchOrderDetails() {
    setLoading(true)
    try {
      // For now, we'll get the order from the orders list
      // In production, you'd have a dedicated endpoint GET /ceo/orders/{orderId}
      const response = await api.get("/ceo/orders", { 
        params: { search: orderId } 
      })
      
      const orders = response.data.data.orders || []
      const foundOrder = orders.find((o: any) => o.order_id === orderId)
      
      if (foundOrder) {
        setOrder(foundOrder)
      } else {
        toast.error("Order not found")
        router.push("/ceo/orders")
      }
    } catch (error: any) {
      toast.error("Failed to load order details")
      if (error.response?.status === 401) {
        router.push("/ceo/login")
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-muted-foreground">Loading order details...</p>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto" />
          <p className="text-lg font-semibold">Order not found</p>
          <Link href="/ceo/orders">
            <Button>Back to Orders</Button>
          </Link>
        </div>
      </div>
    )
  }

  const statusConfig = STATUS_CONFIG[order.order_status] || STATUS_CONFIG.pending
  const StatusIcon = statusConfig.icon

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Link href="/ceo/orders">
                <Button variant="ghost" size="icon">
                  <ArrowLeft className="h-5 w-5" />
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Order Details</h1>
                <p className="text-sm text-muted-foreground mt-1 font-mono">
                  {order.order_id}
                </p>
              </div>
            </div>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${statusConfig.color}`}>
            <StatusIcon className="h-5 w-5" />
            <span className="font-semibold">{statusConfig.label}</span>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Order Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Order Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Order ID</p>
                  <p className="font-mono text-sm font-medium">{order.order_id.substring(0, 16)}...</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Amount</p>
                  <p className="text-lg font-bold text-green-600">₦{order.total_amount.toLocaleString()}</p>
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    Created
                  </p>
                  <p className="text-sm font-medium">
                    {new Date(order.created_at).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                {order.updated_at && (
                  <div>
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Updated
                    </p>
                    <p className="text-sm font-medium">
                      {new Date(order.updated_at).toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                )}
              </div>

              {order.payment_method && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <DollarSign className="h-3 w-3" />
                      Payment Method
                    </p>
                    <p className="text-sm font-medium">{order.payment_method}</p>
                  </div>
                </>
              )}

              {order.delivery_address && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      Delivery Address
                    </p>
                    <p className="text-sm font-medium">{order.delivery_address}</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Buyer & Vendor Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Buyer & Vendor
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-muted-foreground mb-2">Buyer</p>
                <div className="space-y-2 pl-3 border-l-2 border-blue-200">
                  <div>
                    <p className="text-xs text-muted-foreground">Buyer ID</p>
                    <p className="font-medium">{order.buyer_id}</p>
                  </div>
                  {order.buyer_name && (
                    <div>
                      <p className="text-xs text-muted-foreground">Name</p>
                      <p className="font-medium">{order.buyer_name}</p>
                    </div>
                  )}
                  {order.buyer_phone && (
                    <div>
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        Phone
                      </p>
                      <p className="font-medium">{order.buyer_phone}</p>
                    </div>
                  )}
                  {order.buyer_email && (
                    <div>
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        Email
                      </p>
                      <p className="font-medium">{order.buyer_email}</p>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-semibold text-muted-foreground mb-2">Vendor</p>
                <div className="space-y-2 pl-3 border-l-2 border-green-200">
                  <div>
                    <p className="text-xs text-muted-foreground">Vendor Name</p>
                    <p className="font-medium">{order.vendor_name || "Unknown"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Vendor ID</p>
                    <p className="font-mono text-sm">{order.vendor_id.substring(0, 16)}...</p>
                  </div>
                  <Link href={`/ceo/vendors?highlight=${order.vendor_id}`}>
                    <Button variant="outline" size="sm" className="mt-2">
                      View Vendor Details
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Order Items */}
          {order.items && order.items.length > 0 && (
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Order Items
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {order.items.map((item, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <div>
                        <p className="font-medium">{item.item_name}</p>
                        <p className="text-sm text-muted-foreground">Quantity: {item.quantity}</p>
                      </div>
                      <p className="font-semibold">₦{(item.price * item.quantity).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Notes & Receipt */}
          {(order.notes || order.receipt_url) && (
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Additional Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {order.notes && (
                  <div>
                    <p className="text-sm font-semibold text-muted-foreground mb-2">Notes</p>
                    <p className="text-sm bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
                      {order.notes}
                    </p>
                  </div>
                )}

                {order.receipt_url && (
                  <div>
                    <p className="text-sm font-semibold text-muted-foreground mb-2">Payment Receipt</p>
                    <a href={order.receipt_url} target="_blank" rel="noopener noreferrer">
                      <Button variant="outline" className="gap-2">
                        <Download className="h-4 w-4" />
                        View Receipt
                      </Button>
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center">
          <Link href="/ceo/orders">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Orders
            </Button>
          </Link>

          {(order.order_status === "flagged" || order.total_amount >= 1000000) && (
            <Link href={`/ceo/approvals?order=${order.order_id}`}>
              <Button className="gap-2">
                <AlertTriangle className="h-4 w-4" />
                Review for Approval
              </Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
