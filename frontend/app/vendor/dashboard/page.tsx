"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { Package, AlertTriangle, CheckCircle, Users, TrendingUp, ArrowRight, FileImage, MessageCircle } from "lucide-react"
import Link from "next/link"
import { VendorLayout } from "@/components/vendor/layout"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

interface DashboardData {
  vendor_info: {
    vendor_id: string
    name: string
    email: string
    phone: string
  }
  statistics: {
    active_buyers: number
    pending_orders: number
    flagged_receipts: number
    completed_orders: number
  }
  pending_orders: Array<{
    order_id: string
    buyer_id: string
    buyer_name?: string
    total_amount: number
    status: string
    created_at: number
  }>
}

interface ChartDataPoint {
  date: string
  orders: number
}

export default function VendorDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    fetchDashboardData()
    fetchAnalytics()
  }, [])

  async function fetchDashboardData() {
    try {
      const response = await api.get("/vendor/dashboard")
      setData(response.data.data)
    } catch (error: any) {
      toast.error("Failed to load dashboard")
      if (error.response?.status === 401) {
        router.push("/vendor/login")
      }
    } finally {
      setLoading(false)
    }
  }

  async function fetchAnalytics() {
    try {
      const response = await api.get("/vendor/analytics/orders-by-day?days=7")
      const analyticsData = response.data.data.data || []
      setChartData(analyticsData)
    } catch (error) {
      console.error("Failed to load analytics:", error)
    }
  }

  if (loading) {
    return (
      <VendorLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading dashboard...</p>
          </div>
        </div>
      </VendorLayout>
    )
  }

  if (!data) {
    return (
      <VendorLayout>
        <div className="flex items-center justify-center min-h-screen">
          <p className="text-muted-foreground">Error loading dashboard data</p>
        </div>
      </VendorLayout>
    )
  }

  return (
    <VendorLayout>
      <div className="p-8 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            Welcome back, {data?.vendor_info?.name || "Vendor"}!
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Here's what's happening with your business today
          </p>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Buyers</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.statistics?.active_buyers || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Total unique buyers</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Orders</CardTitle>
              <Package className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-500">
                {data.statistics?.pending_orders || 0}
              </div>
              <Link href="/vendor/orders?status=PENDING" className="text-xs text-blue-500 hover:underline mt-1 inline-block">
                View all →
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Flagged Receipts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-500">
                {data.statistics?.flagged_receipts || 0}
              </div>
              <Link href="/vendor/receipts?tab=flagged" className="text-xs text-yellow-600 hover:underline mt-1 inline-block">
                Review now →
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed Orders</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">
                {data.statistics?.completed_orders || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Successfully processed</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push("/vendor/receipts")}>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileImage className="h-5 w-5 text-primary" />
                Verify Receipts
              </CardTitle>
              <CardDescription>Review pending payment receipts</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                Go to Receipts <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push("/vendor/buyers")}>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                Manage Buyers
              </CardTitle>
              <CardDescription>View buyer history and patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Buyers <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push("/vendor/orders")}>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" />
                View All Orders
              </CardTitle>
              <CardDescription>Browse all order history</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Orders <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Recent Chats & Notifications Row */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Recent Conversations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Conversations</CardTitle>
              <CardDescription>Latest buyer interactions</CardDescription>
            </CardHeader>
            <CardContent>
              {data.pending_orders && data.pending_orders.length > 0 ? (
                <div className="space-y-3">
                  {data.pending_orders.slice(0, 5).map((order) => (
                    <Link
                      key={order.order_id}
                      href={`/vendor/negotiation/${order.order_id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors border"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <Users className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{order.buyer_name || "Unknown Buyer"}</p>
                          <p className="text-sm text-muted-foreground">
                            Order #{order.order_id.substring(0, 8)}...
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">
                          ₦{((order.total_amount || 0) / 100).toLocaleString()}
                        </p>
                        <Badge variant="secondary" className="mt-1">
                          {order.status}
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No recent conversations</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Notifications</CardTitle>
              <CardDescription>Latest updates and alerts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.statistics?.flagged_receipts > 0 && (
                  <div className="flex items-start gap-3 p-3 rounded-lg border border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-950/20">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-yellow-900 dark:text-yellow-100">
                        {data.statistics.flagged_receipts} Flagged Receipt{data.statistics.flagged_receipts > 1 ? 's' : ''}
                      </p>
                      <p className="text-sm text-yellow-700 dark:text-yellow-300">
                        Requires immediate review
                      </p>
                    </div>
                  </div>
                )}
                
                {data.statistics?.pending_orders > 0 && (
                  <div className="flex items-start gap-3 p-3 rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/20">
                    <Package className="h-5 w-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-blue-900 dark:text-blue-100">
                        {data.statistics.pending_orders} Pending Order{data.statistics.pending_orders > 1 ? 's' : ''}
                      </p>
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        Awaiting processing
                      </p>
                    </div>
                  </div>
                )}

                {data.statistics?.active_buyers > 0 && (
                  <div className="flex items-start gap-3 p-3 rounded-lg border">
                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="font-medium">
                        {data.statistics.active_buyers} Active Buyer{data.statistics.active_buyers > 1 ? 's' : ''}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Last 30 days
                      </p>
                    </div>
                  </div>
                )}

                {!data.statistics?.flagged_receipts && !data.statistics?.pending_orders && (
                  <div className="text-center py-8 text-muted-foreground">
                    <CheckCircle className="h-12 w-12 mx-auto mb-2 opacity-50 text-green-500" />
                    <p>All caught up!</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Analytics Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Orders Trend (Last 7 Days)
            </CardTitle>
            <CardDescription>Daily order count overview</CardDescription>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorOrders" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="orders"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorOrders)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <p>No analytics data available yet</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Pending Orders */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Pending Orders</CardTitle>
              <Link href="/vendor/orders">
                <Button variant="outline" size="sm">
                  View All <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {data.pending_orders && data.pending_orders.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Buyer</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.pending_orders.slice(0, 5).map((order) => (
                    <TableRow key={order.order_id}>
                      <TableCell className="font-mono text-sm">
                        {order.order_id.substring(0, 12)}...
                      </TableCell>
                      <TableCell>{order.buyer_name || order.buyer_id}</TableCell>
                      <TableCell className="font-semibold">
                        ₦{((order.total_amount || 0) / 100).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            order.status === "APPROVED"
                              ? "default"
                              : order.status === "PENDING"
                              ? "secondary"
                              : "destructive"
                          }
                        >
                          {order.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(order.created_at * 1000).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/vendor/negotiation/${order.order_id}`}>
                          <Button size="sm" variant="outline">
                            Chat
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No pending orders at the moment</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </VendorLayout>
  )
}
