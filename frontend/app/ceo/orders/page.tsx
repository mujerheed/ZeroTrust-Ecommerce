"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { CEOLayout } from "@/components/ceo/CEOLayout"
import { Search, Filter, ArrowLeft, Eye, Package, Calendar } from "lucide-react"
import Link from "next/link"

interface Order {
  order_id: string
  buyer_id: string
  vendor_id: string
  vendor_name: string
  total_amount: number
  order_status: string
  created_at: string
  updated_at?: string
}

interface OrdersResponse {
  orders: Order[]
  total_count: number
  filters_applied: {
    status: string | null
    vendor_id: string | null
    search: string | null
  }
}

interface Vendor {
  user_id: string
  name: string
}

const STATUS_COLORS: { [key: string]: string } = {
  pending: "secondary",
  confirmed: "default",
  paid: "default",
  completed: "default",
  flagged: "destructive",
  rejected: "destructive",
  cancelled: "outline",
}

const STATUS_LABELS: { [key: string]: string } = {
  pending: "Pending",
  confirmed: "Confirmed",
  paid: "Paid",
  completed: "Completed",
  flagged: "Flagged",
  rejected: "Rejected",
  cancelled: "Cancelled",
}

export default function CEOOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [vendorFilter, setVendorFilter] = useState<string>("all")
  const router = useRouter()

  useEffect(() => {
    fetchVendors()
  }, [])

  useEffect(() => {
    fetchOrders()
  }, [statusFilter, vendorFilter])

  async function fetchVendors() {
    try {
      const response = await api.get("/ceo/vendors")
      setVendors(response.data.data.vendors || [])
    } catch (error: any) {
      console.error("Failed to load vendors:", error)
    }
  }

  async function fetchOrders() {
    setLoading(true)
    try {
      const params: any = {}
      
      if (statusFilter !== "all") {
        params.status = statusFilter
      }
      
      if (vendorFilter !== "all") {
        params.vendor_id = vendorFilter
      }
      
      if (search.trim()) {
        params.search = search.trim()
      }

      const response = await api.get("/ceo/orders", { params })
      const data: OrdersResponse = response.data.data
      setOrders(data.orders || [])
    } catch (error: any) {
      toast.error("Failed to load orders")
      if (error.response?.status === 401) {
        router.push("/ceo/login")
      }
    } finally {
      setLoading(false)
    }
  }

  function handleSearchChange(value: string) {
    setSearch(value)
  }

  function handleSearchSubmit() {
    fetchOrders()
  }

  function handleClearFilters() {
    setSearch("")
    setStatusFilter("all")
    setVendorFilter("all")
  }

  const hasActiveFilters = statusFilter !== "all" || vendorFilter !== "all" || search.trim() !== ""

  if (loading && orders.length === 0) {
    return (
      <CEOLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-muted-foreground">Loading orders...</p>
          </div>
        </div>
      </CEOLayout>
    )
  }

  return (
    <CEOLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white">All Orders</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Manage orders across all vendors
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5 text-blue-600" />
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {orders.length}
            </span>
            <span className="text-slate-600 dark:text-slate-400">total orders</span>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters
            </CardTitle>
            <CardDescription>Filter and search orders</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="flex gap-2">
                  <Input
                    placeholder="Search by Order ID or Buyer ID..."
                    value={search}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit()}
                    className="flex-1"
                  />
                  <Button onClick={handleSearchSubmit} size="icon">
                    <Search className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Status Filter */}
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="confirmed">Confirmed</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="flagged">Flagged</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>

              {/* Vendor Filter */}
              <Select value={vendorFilter} onValueChange={setVendorFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Vendors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Vendors</SelectItem>
                  {vendors.map((vendor) => (
                    <SelectItem key={vendor.user_id} value={vendor.user_id}>
                      {vendor.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <div className="mt-4">
                <Button variant="outline" onClick={handleClearFilters} size="sm">
                  Clear All Filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Orders Table */}
        <Card>
          <CardHeader>
            <CardTitle>Orders List</CardTitle>
            <CardDescription>
              {hasActiveFilters ? `Showing ${orders.length} filtered orders` : `Showing all ${orders.length} orders`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {orders.length === 0 ? (
              <div className="text-center py-12">
                <Package className="h-12 w-12 text-slate-400 dark:text-slate-500 mx-auto mb-4" />
                <p className="text-lg font-semibold text-slate-600 dark:text-slate-400">
                  No orders found
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {hasActiveFilters ? "Try adjusting your filters" : "Orders will appear here once vendors create them"}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order ID</TableHead>
                      <TableHead>Buyer</TableHead>
                      <TableHead>Vendor</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order) => (
                      <TableRow key={order.order_id}>
                        <TableCell className="font-mono text-sm">
                          {order.order_id.substring(0, 8)}...
                        </TableCell>
                        <TableCell className="font-medium">
                          {order.buyer_id}
                        </TableCell>
                        <TableCell>{order.vendor_name}</TableCell>
                        <TableCell className="font-semibold">
                          ₦{order.total_amount.toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant={STATUS_COLORS[order.order_status] as any}>
                            {STATUS_LABELS[order.order_status] || order.order_status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            {new Date(order.created_at).toLocaleDateString('en-US', { 
                              year: 'numeric', 
                              month: 'short', 
                              day: 'numeric' 
                            })}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Link href={`/ceo/orders/${order.order_id}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </CEOLayout>
  )
}
