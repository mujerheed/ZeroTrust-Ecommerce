"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { toast } from "sonner"
import {
  User,
  ShoppingCart,
  Users,
  AlertTriangle,
  TrendingUp,
  Phone,
  Mail,
  Calendar,
  DollarSign,
  Package,
  CheckCircle,
  XCircle,
  Clock,
  Coins
} from "lucide-react"

interface VendorDetailModalProps {
  vendorId: string | null
  isOpen: boolean
  onClose: () => void
}

interface VendorDetails {
  vendor: {
    vendor_id: string
    name: string
    email: string
    phone: string
    created_at: number
    updated_at: number
    verified: boolean
    status: string
    risk_score: number
  }
  statistics: {
    total_orders: number
    completed_orders: number
    flagged_orders: number
    pending_orders: number
    total_revenue: number
    unique_buyers: number
  }
  recent_orders: any[]
  buyers: any[]
  flagged_orders: any[]
}

export function VendorDetailModal({ vendorId, isOpen, onClose }: VendorDetailModalProps) {
  const [loading, setLoading] = useState(false)
  const [details, setDetails] = useState<VendorDetails | null>(null)

  useEffect(() => {
    if (isOpen && vendorId) {
      fetchVendorDetails()
    }
  }, [isOpen, vendorId])

  async function fetchVendorDetails() {
    if (!vendorId) return
    
    setLoading(true)
    try {
      const response = await api.get(`/ceo/vendors/${vendorId}/details`)
      setDetails(response.data.data.details)
    } catch (error: any) {
      toast.error("Failed to load vendor details")
      console.error("Fetch vendor details error:", error)
    } finally {
      setLoading(false)
    }
  }

  function formatDate(timestamp: number) {
    return new Date(timestamp * 1000).toLocaleDateString("en-NG", {
      year: "numeric",
      month: "short",
      day: "numeric"
    })
  }

  function formatCurrency(amount: number) {
    return `₦${amount.toLocaleString("en-NG", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  function getStatusBadge(status: string) {
    const statusConfig: Record<string, { variant: "default" | "secondary" | "destructive" | "outline", icon: any }> = {
      completed: { variant: "default", icon: CheckCircle },
      pending: { variant: "secondary", icon: Clock },
      pending_receipt: { variant: "secondary", icon: Clock },
      flagged: { variant: "destructive", icon: AlertTriangle },
      rejected: { variant: "destructive", icon: XCircle }
    }
    
    const config = statusConfig[status] || { variant: "outline" as const, icon: Package }
    const Icon = config.icon
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {status.replace("_", " ").toUpperCase()}
      </Badge>
    )
  }

  if (!isOpen || !vendorId) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl flex items-center gap-2">
            <User className="h-6 w-6" />
            {details ? details.vendor.name : "Vendor Details"}
          </DialogTitle>
          <DialogDescription>
            Complete vendor information, order history, and performance metrics
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900" />
          </div>
        ) : details ? (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="orders">Orders</TabsTrigger>
              <TabsTrigger value="buyers">Buyers</TabsTrigger>
              <TabsTrigger value="flags">Flags</TabsTrigger>
            </TabsList>

            {/* OVERVIEW TAB */}
            <TabsContent value="overview" className="space-y-4">
              {/* Vendor Info Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Vendor Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-gray-500" />
                    <div>
                      <p className="text-sm text-gray-500">Email</p>
                      <p className="font-medium">{details.vendor.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-gray-500" />
                    <div>
                      <p className="text-sm text-gray-500">Phone</p>
                      <p className="font-medium">{details.vendor.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-gray-500" />
                    <div>
                      <p className="text-sm text-gray-500">Joined</p>
                      <p className="font-medium">{formatDate(details.vendor.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-gray-500" />
                    <div>
                      <p className="text-sm text-gray-500">Status</p>
                      <Badge variant={details.vendor.verified ? "default" : "secondary"}>
                        {details.vendor.status}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Statistics Grid */}
              <div className="grid grid-cols-3 gap-4">
                <Card className="border-blue-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <ShoppingCart className="h-4 w-4 text-blue-600" />
                      Total Orders
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-blue-600">{details.statistics.total_orders}</p>
                    <p className="text-xs text-gray-500 mt-1">All time</p>
                  </CardContent>
                </Card>

                <Card className="border-green-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <Coins className="h-4 w-4 text-green-600" />
                      Total Revenue
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-green-600">{formatCurrency(details.statistics.total_revenue)}</p>
                    <p className="text-xs text-gray-500 mt-1">{details.statistics.completed_orders} completed</p>
                  </CardContent>
                </Card>

                <Card className="border-purple-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <Users className="h-4 w-4 text-purple-600" />
                      Unique Buyers
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-purple-600">{details.statistics.unique_buyers}</p>
                    <p className="text-xs text-gray-500 mt-1">Customer base</p>
                  </CardContent>
                </Card>

                <Card className="border-orange-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      Flagged Orders
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-orange-600">{details.statistics.flagged_orders}</p>
                    <p className="text-xs text-gray-500 mt-1">Needs attention</p>
                  </CardContent>
                </Card>

                <Card className="border-yellow-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <Clock className="h-4 w-4 text-yellow-600" />
                      Pending Orders
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-yellow-600">{details.statistics.pending_orders}</p>
                    <p className="text-xs text-gray-500 mt-1">In progress</p>
                  </CardContent>
                </Card>

                <Card className="border-red-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-red-600" />
                      Risk Score
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-red-600">{details.vendor.risk_score.toFixed(1)}%</p>
                    <p className="text-xs text-gray-500 mt-1">Fraud indicator</p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* ORDERS TAB */}
            <TabsContent value="orders" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Orders</CardTitle>
                  <CardDescription>Last 20 orders from this vendor</CardDescription>
                </CardHeader>
                <CardContent>
                  {details.recent_orders.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No orders yet</p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Order ID</TableHead>
                          <TableHead>Buyer</TableHead>
                          <TableHead>Amount</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Date</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {details.recent_orders.map((order) => (
                          <TableRow key={order.order_id}>
                            <TableCell className="font-mono text-xs">{order.order_id?.slice(0, 8)}...</TableCell>
                            <TableCell>{order.buyer_name || "Unknown"}</TableCell>
                            <TableCell className="font-semibold">{formatCurrency(order.amount || 0)}</TableCell>
                            <TableCell>{getStatusBadge(order.order_status)}</TableCell>
                            <TableCell className="text-sm">{formatDate(order.created_at)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* BUYERS TAB */}
            <TabsContent value="buyers" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Unique Buyers</CardTitle>
                  <CardDescription>Customers who have purchased from this vendor</CardDescription>
                </CardHeader>
                <CardContent>
                  {details.buyers.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No buyers yet</p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Buyer Name</TableHead>
                          <TableHead>Phone</TableHead>
                          <TableHead>Total Orders</TableHead>
                          <TableHead>Total Spent</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {details.buyers.map((buyer) => (
                          <TableRow key={buyer.buyer_id}>
                            <TableCell className="font-medium">{buyer.buyer_name}</TableCell>
                            <TableCell className="text-sm">{buyer.phone || "N/A"}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{buyer.total_orders}</Badge>
                            </TableCell>
                            <TableCell className="font-semibold">{formatCurrency(buyer.total_spent)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* FLAGS TAB */}
            <TabsContent value="flags" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                    Flagged Orders
                  </CardTitle>
                  <CardDescription>Orders requiring attention or review</CardDescription>
                </CardHeader>
                <CardContent>
                  {details.flagged_orders.length === 0 ? (
                    <div className="text-center py-8">
                      <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
                      <p className="text-gray-500">No flagged orders - all clear! ✅</p>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Order ID</TableHead>
                          <TableHead>Buyer</TableHead>
                          <TableHead>Amount</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Date</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {details.flagged_orders.map((order) => (
                          <TableRow key={order.order_id} className="bg-orange-50">
                            <TableCell className="font-mono text-xs">{order.order_id?.slice(0, 8)}...</TableCell>
                            <TableCell>{order.buyer_name || "Unknown"}</TableCell>
                            <TableCell className="font-semibold">{formatCurrency(order.amount || 0)}</TableCell>
                            <TableCell>{getStatusBadge(order.order_status)}</TableCell>
                            <TableCell className="text-sm">{formatDate(order.created_at)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        ) : (
          <p className="text-center text-gray-500 py-8">No data available</p>
        )}
      </DialogContent>
    </Dialog>
  )
}
