"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api, clearToken } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { LogOut, Users, AlertTriangle, Activity, TrendingUp, ShoppingCart, Coins, Settings, Plug } from "lucide-react"
import Link from "next/link"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts"
import { CEOLayout } from "@/components/ceo/CEOLayout"

interface CEODashboardData {
  total_vendors: number
  total_orders: number
  total_revenue: number
  pending_approvals: number
  orders_by_status: {
    [key: string]: number
  }
}

interface CEODashboardResponse {
  dashboard: CEODashboardData
  ceo_name: string
}

const STATUS_COLORS: { [key: string]: string } = {
  pending: "#f59e0b",
  completed: "#10b981",
  paid: "#3b82f6",
  flagged: "#ef4444",
  rejected: "#6b7280",
  unknown: "#9ca3af"
}

export default function CEODashboard() {
  const [data, setData] = useState<CEODashboardData | null>(null)
  const [ceoName, setCeoName] = useState<string>("CEO")
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    fetchDashboardData()
  }, [])

  async function fetchDashboardData() {
    try {
      const response = await api.get("/ceo/dashboard")
      const responseData = response.data.data as CEODashboardResponse
      setData(responseData.dashboard)
      setCeoName(responseData.ceo_name || "CEO")
    } catch (error: any) {
      toast.error("Failed to load dashboard")
      if (error.response?.status === 401) {
        router.push("/ceo/login")
      }
    } finally {
      setLoading(false)
    }
  }

  function handleLogout() {
    clearToken()
    router.push("/")
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <AlertTriangle className="h-12 w-12 text-red-500" />
        <p className="text-lg font-semibold">Error loading dashboard data</p>
        <div className="flex gap-3">
          <Button onClick={fetchDashboardData}>Retry</Button>
          <Button variant="outline" onClick={handleLogout}>Logout</Button>
        </div>
      </div>
    )
  }

  const pieChartData = Object.entries(data.orders_by_status).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: STATUS_COLORS[status] || STATUS_COLORS.unknown
  }))

  const barChartData = Object.entries(data.orders_by_status).map(([status, count]) => ({
    status: status.charAt(0).toUpperCase() + status.slice(1),
    count: count
  }))

  return (
    <CEOLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white">Welcome back, {ceoName}!</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">TrustGuard Zero Trust System</p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-l-4 border-l-blue-500 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Vendors</CardTitle>
              <Users className="h-5 w-5 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">{data.total_vendors}</div>
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                Active vendors
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-green-500 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Orders</CardTitle>
              <ShoppingCart className="h-5 w-5 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">{data.total_orders}</div>
              <p className="text-xs text-muted-foreground mt-1">All-time transactions</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-emerald-500 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Revenue</CardTitle>
              <Coins className="h-5 w-5 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                ₦{data.total_revenue.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Completed payments</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-orange-500 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Pending Approvals</CardTitle>
              <AlertTriangle className="h-5 w-5 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-500">{data.pending_approvals}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {data.pending_approvals > 0 ? "Action required" : "All clear"}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-500" /> Orders by Status
              </CardTitle>
              <CardDescription>Distribution of order statuses</CardDescription>
            </CardHeader>
            <CardContent>
              {pieChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  No orders yet
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-500" /> Order Volume
              </CardTitle>
              <CardDescription>Count by status</CardDescription>
            </CardHeader>
            <CardContent>
              {barChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={barChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="status" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  No orders yet
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Manage your TrustGuard system</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            <Link href="/ceo/vendors" className="block">
              <Button className="w-full h-20 flex flex-col gap-2" variant="outline">
                <Users className="h-6 w-6" />
                <span>Manage Vendors</span>
              </Button>
            </Link>
            <Link href="/ceo/approvals" className="block">
              <Button className="w-full h-20 flex flex-col gap-2" variant="outline">
                <AlertTriangle className="h-6 w-6" />
                <span>Approvals</span>
                {data.pending_approvals > 0 && (
                  <Badge variant="destructive">{data.pending_approvals}</Badge>
                )}
              </Button>
            </Link>
            <Link href="/ceo/audit-logs" className="block">
              <Button className="w-full h-20 flex flex-col gap-2" variant="outline">
                <Activity className="h-6 w-6" />
                <span>Audit Logs</span>
              </Button>
            </Link>
            <Link href="/ceo/settings" className="block">
              <Button className="w-full h-20 flex flex-col gap-2" variant="outline">
                <Settings className="h-6 w-6" />
                <span>Settings</span>
              </Button>
            </Link>
            <Link href="/ceo/integrations" className="block">
              <Button className="w-full h-20 flex flex-col gap-2" variant="outline">
                <Plug className="h-6 w-6" />
                <span>Integrations</span>
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </CEOLayout>
  )
}
