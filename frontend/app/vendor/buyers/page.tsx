"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { VendorLayout } from "@/components/vendor/layout"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { toast } from "sonner"
import {
  Users,
  Search,
  AlertTriangle,
  CheckCircle,
  ArrowUpDown,
  Eye,
  Phone,
  Package,
  Calendar,
} from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

interface Buyer {
  buyer_id: string
  phone: string
  name?: string
  total_orders: number
  last_interaction: number
  flagged_count: number
  flag_status: "flagged" | "clean"
}

interface BuyerDetails extends Buyer {
  orders: Array<{
    order_id: string
    total_amount: number
    status: string
    created_at: number
  }>
  statistics: {
    total_orders: number
    completed_orders: number
    flagged_orders: number
    pending_orders: number
    first_order_date: number
    last_order_date: number
  }
}

export default function BuyersManagementPage() {
  const [buyers, setBuyers] = useState<Buyer[]>([])
  const [filteredBuyers, setFilteredBuyers] = useState<Buyer[]>([])
  const [selectedBuyer, setSelectedBuyer] = useState<BuyerDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [showFlaggedOnly, setShowFlaggedOnly] = useState(false)
  const [sortBy, setSortBy] = useState<"orders" | "recent">("recent")
  const [isDetailsOpen, setIsDetailsOpen] = useState(false)
  const router = useRouter()

  useEffect(() => {
    fetchBuyers()
  }, [showFlaggedOnly])

  useEffect(() => {
    filterBuyers()
  }, [buyers, searchQuery, sortBy])

  async function fetchBuyers() {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (showFlaggedOnly) params.append("flag_status", "flagged")
      params.append("limit", "100")

      const response = await api.get(`/vendor/buyers?${params.toString()}`)
      const data = response.data.data
      const buyersList = Array.isArray(data) ? data : (data.buyers || [])
      setBuyers(buyersList)
    } catch (error: any) {
      console.error("Failed to load buyers:", error)
      toast.error(error.response?.data?.message || "Failed to load buyers")
      if (error.response?.status === 401) {
        router.push("/vendor/login")
      }
    } finally {
      setLoading(false)
    }
  }

  function filterBuyers() {
    let filtered = [...buyers]

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (buyer) =>
          buyer.buyer_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          buyer.phone.includes(searchQuery) ||
          (buyer.name && buyer.name.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    // Sort
    if (sortBy === "orders") {
      filtered.sort((a, b) => b.total_orders - a.total_orders)
    } else {
      filtered.sort((a, b) => b.last_interaction - a.last_interaction)
    }

    setFilteredBuyers(filtered)
  }

  async function viewBuyerDetails(buyer_id: string) {
    try {
      console.log("[Buyers] Fetching details for buyer:", buyer_id)
      const response = await api.get(`/vendor/buyers/${buyer_id}`)
      console.log("[Buyers] Buyer details response:", response.data)
      
      setSelectedBuyer(response.data.data)
      setIsDetailsOpen(true)
    } catch (error: any) {
      console.error("[Buyers] Failed to load buyer details:", error)
      console.error("[Buyers] Error response:", error.response?.data)
      toast.error(error.response?.data?.message || error.response?.data?.detail || "Failed to load buyer details")
    }
  }

  function formatTimeAgo(timestamp: number): string {
    if (timestamp === 0) return "Never"
    
    const now = Math.floor(Date.now() / 1000)
    const diff = now - timestamp
    const days = Math.floor(diff / 86400)
    const hours = Math.floor(diff / 3600)
    const minutes = Math.floor(diff / 60)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return "Just now"
  }

  if (loading) {
    return (
      <VendorLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading buyers...</p>
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
        <div>
          <h1 className="text-3xl font-bold text-foreground">Buyers Management</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Track buyer activity and identify patterns
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Buyers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{buyers.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Flagged Buyers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {buyers.filter((b) => b.flag_status === "flagged").length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Buyers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {buyers.filter((b) => b.flag_status === "clean").length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {buyers.reduce((sum, b) => sum + b.total_orders, 0)}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by buyer ID, phone, or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Show Flagged Only */}
              <div className="flex items-center space-x-2 border rounded-lg px-4">
                <Switch
                  id="flagged-only"
                  checked={showFlaggedOnly}
                  onCheckedChange={setShowFlaggedOnly}
                />
                <Label htmlFor="flagged-only" className="cursor-pointer">
                  Show Flagged Only
                </Label>
              </div>

              {/* Sort */}
              <Button
                variant="outline"
                onClick={() => setSortBy(sortBy === "orders" ? "recent" : "orders")}
              >
                <ArrowUpDown className="mr-2 h-4 w-4" />
                Sort by {sortBy === "orders" ? "Recent" : "Orders"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Buyers Table */}
        <Card>
          <CardHeader>
            <CardTitle>
              {showFlaggedOnly ? "Flagged Buyers" : "All Buyers"} ({filteredBuyers.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredBuyers.length === 0 ? (
              <div className="text-center py-12">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-lg font-medium">No buyers found</p>
                <p className="text-sm text-muted-foreground mt-2">
                  {searchQuery
                    ? "Try a different search query"
                    : showFlaggedOnly
                    ? "No flagged buyers at the moment"
                    : "No buyers have placed orders yet"}
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Buyer</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead className="text-center">Total Orders</TableHead>
                    <TableHead className="text-center">Flagged</TableHead>
                    <TableHead>Last Interaction</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredBuyers.map((buyer) => (
                    <TableRow key={buyer.buyer_id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">
                            {buyer.name || "Unknown Buyer"}
                          </p>
                          <p className="text-xs text-muted-foreground font-mono">
                            {buyer.buyer_id}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Phone className="h-3 w-3 text-muted-foreground" />
                          <span className="font-mono text-sm">{buyer.phone}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="secondary">{buyer.total_orders}</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        {buyer.flagged_count > 0 ? (
                          <Badge variant="destructive">{buyer.flagged_count}</Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">
                          {formatTimeAgo(buyer.last_interaction)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {buyer.flag_status === "flagged" ? (
                          <Badge variant="outline" className="border-yellow-600 text-yellow-600">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Flagged
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="border-green-600 text-green-600">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Clean
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewBuyerDetails(buyer.buyer_id)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Buyer Details Dialog */}
        <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center justify-between">
                <span>Buyer Details</span>
                {selectedBuyer && (
                  selectedBuyer.flag_status === "flagged" ? (
                    <Badge variant="outline" className="border-yellow-600 text-yellow-600">
                      <AlertTriangle className="h-3 w-3 mr-1" />
                      Flagged
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="border-green-600 text-green-600">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Clean
                    </Badge>
                  )
                )}
              </DialogTitle>
              <DialogDescription>
                {selectedBuyer?.buyer_id}
              </DialogDescription>
            </DialogHeader>

            {selectedBuyer && (
              <div className="space-y-6">
                {/* Buyer Info */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Buyer Information</CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Name</p>
                      <p className="font-medium">{selectedBuyer.name || "Unknown"}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Phone</p>
                      <p className="font-mono">{selectedBuyer.phone}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">First Order</p>
                      <p className="text-sm">
                        {selectedBuyer.statistics.first_order_date
                          ? new Date(selectedBuyer.statistics.first_order_date * 1000).toLocaleDateString()
                          : "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Last Order</p>
                      <p className="text-sm">
                        {selectedBuyer.statistics.last_order_date
                          ? new Date(selectedBuyer.statistics.last_order_date * 1000).toLocaleDateString()
                          : "N/A"}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        Total Orders
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {selectedBuyer.statistics.total_orders}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        Completed
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">
                        {selectedBuyer.statistics.completed_orders}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        Pending
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-blue-600">
                        {selectedBuyer.statistics.pending_orders}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        Flagged
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-yellow-600">
                        {selectedBuyer.statistics.flagged_orders}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Orders */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Recent Orders</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {selectedBuyer.orders.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No orders found
                      </p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Order ID</TableHead>
                            <TableHead>Amount</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Date</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {selectedBuyer.orders.map((order) => (
                            <TableRow key={order.order_id}>
                              <TableCell className="font-mono text-sm">
                                {order.order_id}
                              </TableCell>
                              <TableCell className="font-semibold">
                                ₦{(order.total_amount / 100).toLocaleString()}
                              </TableCell>
                              <TableCell>
                                <Badge variant={
                                  order.status === "APPROVED" ? "default" :
                                  order.status === "PENDING" ? "secondary" : "destructive"
                                }>
                                  {order.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-sm">
                                {new Date(order.created_at * 1000).toLocaleDateString()}
                              </TableCell>
                              <TableCell className="text-right">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setIsDetailsOpen(false)
                                    router.push(`/vendor/negotiation/${order.order_id}`)
                                  }}
                                >
                                  View
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
    </VendorLayout>
  )
}
