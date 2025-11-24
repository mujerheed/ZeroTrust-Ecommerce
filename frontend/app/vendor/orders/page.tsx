"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { Package, Search, MessageCircle, Eye } from "lucide-react"
import Link from "next/link"
import { VendorLayout } from "@/components/vendor/layout"

interface Order {
  order_id: string
  buyer_id: string
  buyer_name?: string
  total_amount: number
  status: string
  created_at: number
  receipt_status?: string
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const statusParam = searchParams.get("status")
    if (statusParam) {
      setStatusFilter(statusParam.toLowerCase())
    }
    fetchOrders()
  }, [])

  useEffect(() => {
    filterOrders()
  }, [orders, searchQuery, statusFilter])

  async function fetchOrders() {
    try {
      setLoading(true)
      console.log("[Orders] Fetching orders from /vendor/orders")
      
      const token = localStorage.getItem('token')
      console.log("[Orders] Token exists:", !!token)
      
      const response = await api.get("/vendor/orders")
      console.log("[Orders] Response status:", response.status)
      console.log("[Orders] Response data:", response.data)
      
      const data = response.data.data
      // Handle both array and object responses
      const ordersList = Array.isArray(data) ? data : (data.orders || [])
      console.log("[Orders] Processed orders count:", ordersList.length)
      setOrders(ordersList)
    } catch (error: any) {
      console.error("[Orders] Failed to load orders:", error)
      console.error("[Orders] Error response:", error.response?.data)
      console.error("[Orders] Error status:", error.response?.status)
      console.error("[Orders] Error headers:", error.response?.headers)
      
      toast.error(error.response?.data?.message || error.response?.data?.detail || "Failed to load orders")
      
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.")
        router.push("/vendor/login")
      }
    } finally {
      setLoading(false)
    }
  }

  function filterOrders() {
    let filtered = [...orders]

    // Apply status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter(
        (order) => order.status.toLowerCase() === statusFilter
      )
    }

    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (order) =>
          order.order_id.toLowerCase().includes(query) ||
          order.buyer_id.toLowerCase().includes(query) ||
          order.buyer_name?.toLowerCase().includes(query)
      )
    }

    setFilteredOrders(filtered)
  }

  function getStatusBadgeVariant(status: string) {
    switch (status.toUpperCase()) {
      case "COMPLETED":
      case "APPROVED":
        return "default"
      case "PENDING":
      case "PENDING_RECEIPT":
        return "secondary"
      case "FLAGGED":
        return "destructive"
      case "REJECTED":
        return "outline"
      default:
        return "secondary"
    }
  }

  if (loading) {
    return (
      <VendorLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading orders...</p>
          </div>
        </div>
      </VendorLayout>
    )
  }

  return (
    <VendorLayout>
      <div className="p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-foreground">All Orders</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Manage and track all your orders
              </p>
            </div>
          </div>

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Filters</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 flex-wrap">
                {/* Search */}
                <div className="flex-1 min-w-[250px]">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search by order ID, buyer ID, or name..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Status Filter */}
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="pending_receipt">Pending Receipt</SelectItem>
                    <SelectItem value="approved">Approved</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="flagged">Flagged</SelectItem>
                    <SelectItem value="rejected">Rejected</SelectItem>
                  </SelectContent>
                </Select>

                {/* Clear Filters */}
                {(searchQuery || statusFilter !== "all") && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSearchQuery("")
                      setStatusFilter("all")
                    }}
                  >
                    Clear Filters
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Orders
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{orders.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Pending
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {orders.filter((o) => o.status === "PENDING").length}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Completed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {orders.filter((o) => o.status === "COMPLETED").length}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Flagged
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {orders.filter((o) => o.status === "FLAGGED").length}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Orders Table */}
          <Card>
            <CardHeader>
              <CardTitle>
                Orders List ({filteredOrders.length}{" "}
                {filteredOrders.length === 1 ? "order" : "orders"})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filteredOrders.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order ID</TableHead>
                      <TableHead>Buyer</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredOrders.map((order) => (
                      <TableRow key={order.order_id}>
                        <TableCell className="font-mono text-sm">
                          {order.order_id.substring(0, 12)}...
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">
                              {order.buyer_name || "Unknown"}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {order.buyer_id.substring(0, 15)}...
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="font-semibold">
                          ₦{((order.total_amount || 0) / 100).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(order.status)}>
                            {order.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(order.created_at * 1000).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Link href={`/vendor/negotiation/${order.order_id}`}>
                              <Button size="sm" variant="outline">
                                <MessageCircle className="h-4 w-4 mr-1" />
                                Chat
                              </Button>
                            </Link>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                // View order details (could open a modal)
                                toast.info("Order details view coming soon")
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">No orders found</p>
                  <p className="text-sm">
                    {searchQuery || statusFilter !== "all"
                      ? "Try adjusting your filters"
                      : "Orders will appear here once buyers place them"}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </VendorLayout>
  )
}
