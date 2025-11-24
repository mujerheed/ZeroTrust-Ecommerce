"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { toast } from "sonner"
import { VendorLayout } from "@/components/vendor/layout"
import {
  CheckCircle,
  AlertTriangle,
  X,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  Maximize2,
  FileImage,
  Calendar,
  DollarSign,
  Hash,
  TrendingUp,
} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface Receipt {
  receipt_id: string
  order_id: string
  buyer_id: string
  upload_timestamp: number
  s3_key: string
  s3_url: string
  status: "pending_review" | "approved" | "rejected" | "flagged"
  amount: number
  checksum?: string  // SHA-256 hash of receipt file
  textract_data?: {
    amount_detected: number
    date_detected: string
    bank_name: string
    reference_number: string
    confidence_score: number
  }
  order_details?: {
    buyer_name: string
    expected_amount: number
    created_at: number
  }
}

export default function ReceiptVerificationPage() {
  const [activeTab, setActiveTab] = useState<"pending" | "approved" | "flagged">("pending")
  const [receipts, setReceipts] = useState<Receipt[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [notes, setNotes] = useState("")
  const [manualChecks, setManualChecks] = useState({
    amount: false,
    date: false,
    bank: false,
  })
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [textractEnabled, setTextractEnabled] = useState(true)
  const router = useRouter()

  const currentReceipt = receipts[currentIndex]

  useEffect(() => {
    fetchReceipts()
    fetchPreferences()
  }, [activeTab])

  async function fetchReceipts() {
    try {
      setLoading(true)
      const statusMap = {
        pending: "pending_review",
        approved: "approved",
        flagged: "flagged",
      }
      
      // Fetch orders to get receipts
      const response = await api.get("/vendor/orders")
      const data = response.data.data
      const orders = Array.isArray(data) ? data : (data.orders || [])
      
      // Mock receipts from orders - in production, use GET /vendor/receipts
      const mockReceipts: Receipt[] = orders
        .filter((order: any) => {
          // Show all orders for now if no receipt_status field exists
          return true // In real implementation: order.receipt_status === statusMap[activeTab]
        })
        .map((order: any) => ({
          receipt_id: `rcpt_${order.order_id}`,
          order_id: order.order_id,
          buyer_id: order.buyer_id,
          upload_timestamp: order.updated_at || order.created_at,
          s3_key: `receipts/${order.order_id}/receipt.jpg`,
          s3_url: `https://trustguard-receipts.s3.amazonaws.com/receipts/${order.order_id}/receipt.jpg`,
          status: order.receipt_status || "pending_review",
          amount: order.total_amount,
          textract_data: textractEnabled ? {
            amount_detected: Math.floor(order.total_amount * 0.98), // Simulated OCR
            date_detected: new Date((order.created_at || Date.now() / 1000) * 1000).toISOString().split('T')[0],
            bank_name: "GTBank",
            reference_number: `TXN${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
            confidence_score: 0.87,
          } : undefined,
          order_details: {
            buyer_name: order.buyer_name || "Unknown Buyer",
            expected_amount: order.total_amount,
            created_at: order.created_at || Math.floor(Date.now() / 1000),
          },
        }))
      
      setReceipts(mockReceipts)
      setCurrentIndex(0)
    } catch (error: any) {
      toast.error("Failed to load receipts")
      if (error.response?.status === 401) {
        router.push("/vendor/login")
      }
    } finally {
      setLoading(false)
    }
  }

  async function fetchPreferences() {
    try {
      const response = await api.get("/vendor/preferences")
      setTextractEnabled(response.data.data.textract_enabled || false)
    } catch (error) {
      console.error("Failed to fetch preferences:", error)
    }
  }

  async function handleVerifyReceipt(action: "approve" | "flag" | "reject") {
    if (!currentReceipt) return

    try {
      await api.post(`/vendor/orders/${currentReceipt.order_id}/verify`, {
        action,
        notes: notes || undefined,
      })

      const actionText = action === "approve" ? "approved" : action === "flag" ? "flagged for CEO review" : "rejected"
      toast.success(`Receipt ${actionText} successfully`)

      // Move to next receipt
      if (currentIndex < receipts.length - 1) {
        setCurrentIndex(currentIndex + 1)
      } else {
        // Refresh list if last receipt
        fetchReceipts()
      }

      // Reset form
      setNotes("")
      setManualChecks({ amount: false, date: false, bank: false })
    } catch (error: any) {
      toast.error(error.response?.data?.message || `Failed to ${action} receipt`)
    }
  }

  function navigateReceipt(direction: "prev" | "next") {
    if (direction === "prev" && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    } else if (direction === "next" && currentIndex < receipts.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  // Keyboard navigation
  useEffect(() => {
    function handleKeyPress(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" && currentIndex > 0) {
        setCurrentIndex(currentIndex - 1)
      }
      if (e.key === "ArrowRight" && currentIndex < receipts.length - 1) {
        setCurrentIndex(currentIndex + 1)
      }
    }
    window.addEventListener("keydown", handleKeyPress)
    return () => window.removeEventListener("keydown", handleKeyPress)
  }, [currentIndex, receipts.length])

  if (loading) {
    return (
      <VendorLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading receipts...</p>
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
          <h1 className="text-3xl font-bold text-foreground">Receipt Verification</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Review and verify payment receipts
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
          <TabsList className="grid w-full grid-cols-3 max-w-md">
            <TabsTrigger value="pending">
              Pending ({receipts.filter(r => r.status === "pending_review").length})
            </TabsTrigger>
            <TabsTrigger value="approved">
              Approved ({receipts.filter(r => r.status === "approved").length})
            </TabsTrigger>
            <TabsTrigger value="flagged">
              Flagged ({receipts.filter(r => r.status === "flagged").length})
            </TabsTrigger>
          </TabsList>

          {receipts.length === 0 ? (
            <Card className="mt-6">
              <CardContent className="py-12 text-center">
                <FileImage className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-lg font-medium">No {activeTab} receipts</p>
                <p className="text-sm text-muted-foreground mt-2">
                  {activeTab === "pending" && "All receipts have been reviewed"}
                  {activeTab === "approved" && "No receipts have been approved yet"}
                  {activeTab === "flagged" && "No receipts have been flagged"}
                </p>
              </CardContent>
            </Card>
          ) : (
            <TabsContent value={activeTab} className="mt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Receipt Image Section */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Receipt Image</span>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setIsFullscreen(true)}
                        >
                          <Maximize2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="relative aspect-[3/4] bg-muted rounded-lg overflow-hidden">
                      {currentReceipt?.s3_url ? (
                        <img
                          src={currentReceipt.s3_url}
                          alt="Receipt"
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            // Fallback to placeholder if image fails
                            e.currentTarget.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='600'%3E%3Crect fill='%23e5e7eb' width='400' height='600'/%3E%3Ctext fill='%236b7280' font-family='sans-serif' font-size='24' x='50%25' y='50%25' text-anchor='middle' dominant-baseline='middle'%3EReceipt Image%3C/text%3E%3C/svg%3E"
                          }}
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center">
                            <FileImage className="h-16 w-16 text-muted-foreground mx-auto mb-2" />
                            <p className="text-sm text-muted-foreground">No image available</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Order Info */}
                    <div className="mt-4 space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Order ID:</span>
                        <span className="font-mono">{currentReceipt?.order_id}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Buyer:</span>
                        <span>{currentReceipt?.order_details?.buyer_name}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Expected Amount:</span>
                        <span className="font-semibold">
                          ₦{((currentReceipt?.order_details?.expected_amount || 0) / 100).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Uploaded:</span>
                        <span>
                          {currentReceipt?.upload_timestamp && 
                            new Date(currentReceipt.upload_timestamp * 1000).toLocaleString()}
                        </span>
                      </div>
                      {currentReceipt?.checksum && (
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Checksum:</span>
                          <span className="font-mono text-xs truncate max-w-[200px]" title={currentReceipt.checksum}>
                            {currentReceipt.checksum.substring(0, 16)}...
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Verification Details Section */}
                <div className="space-y-6">
                  {/* Amount Mismatch Warning */}
                  {textractEnabled && currentReceipt?.textract_data && 
                   Math.abs((currentReceipt.textract_data.amount_detected || 0) - (currentReceipt.order_details?.expected_amount || 0)) >= 100 && (
                    <Card className="border-orange-500 bg-orange-50 dark:bg-orange-950/20">
                      <CardContent className="pt-6">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400 mt-0.5" />
                          <div className="flex-1">
                            <h4 className="font-semibold text-orange-900 dark:text-orange-100">Amount Mismatch Detected</h4>
                            <p className="text-sm text-orange-800 dark:text-orange-200 mt-1">
                              The amount detected by OCR (₦{((currentReceipt.textract_data.amount_detected || 0) / 100).toLocaleString()}) 
                              does not match the expected amount (₦{((currentReceipt.order_details?.expected_amount || 0) / 100).toLocaleString()}).
                              Please verify manually before approval.
                            </p>
                            {currentReceipt.textract_data.confidence_score < 0.7 && (
                              <p className="text-sm text-orange-700 dark:text-orange-300 mt-2">
                                ⚠️ Low OCR confidence ({(currentReceipt.textract_data.confidence_score * 100).toFixed(0)}%) - Manual review strongly recommended.
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Textract OCR Results */}
                  {textractEnabled && currentReceipt?.textract_data && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <TrendingUp className="h-5 w-5" />
                          Textract OCR Analysis
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">Detected Amount:</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">
                              ₦{((currentReceipt.textract_data.amount_detected || 0) / 100).toLocaleString()}
                            </span>
                            {Math.abs((currentReceipt.textract_data.amount_detected || 0) - (currentReceipt.order_details?.expected_amount || 0)) < 100 ? (
                              <Badge variant="default" className="bg-green-500">
                                <CheckCircle className="h-3 w-3 mr-1" /> Match
                              </Badge>
                            ) : (
                              <Badge variant="destructive">
                                <AlertTriangle className="h-3 w-3 mr-1" /> Mismatch
                              </Badge>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">Date:</span>
                          </div>
                          <span className="font-medium">{currentReceipt.textract_data.date_detected}</span>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Hash className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">Reference:</span>
                          </div>
                          <span className="font-mono text-sm">{currentReceipt.textract_data.reference_number}</span>
                        </div>

                        <div className="pt-4 border-t">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Confidence Score:</span>
                            <Badge variant={
                              currentReceipt.textract_data.confidence_score >= 0.9 ? "default" :
                              currentReceipt.textract_data.confidence_score >= 0.7 ? "secondary" : "destructive"
                            }>
                              {(currentReceipt.textract_data.confidence_score * 100).toFixed(0)}%
                            </Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Manual Review */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Manual Review</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="check-amount"
                            checked={manualChecks.amount}
                            onCheckedChange={(checked: boolean) =>
                              setManualChecks({ ...manualChecks, amount: !!checked })
                            }
                          />
                          <label
                            htmlFor="check-amount"
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                          >
                            Amount verified
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="check-date"
                            checked={manualChecks.date}
                            onCheckedChange={(checked: boolean) =>
                              setManualChecks({ ...manualChecks, date: !!checked })
                            }
                          />
                          <label
                            htmlFor="check-date"
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                          >
                            Date correct
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="check-bank"
                            checked={manualChecks.bank}
                            onCheckedChange={(checked: boolean) =>
                              setManualChecks({ ...manualChecks, bank: !!checked })
                            }
                          />
                          <label
                            htmlFor="check-bank"
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                          >
                            Bank details match
                          </label>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="notes">Notes (optional)</Label>
                        <Textarea
                          id="notes"
                          placeholder="Add notes about this verification..."
                          value={notes}
                          onChange={(e) => setNotes(e.target.value)}
                          rows={3}
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2 pt-4">
                        <Button
                          className="flex-1 bg-green-600 hover:bg-green-700"
                          onClick={() => handleVerifyReceipt("approve")}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          className="flex-1 border-yellow-600 text-yellow-600 hover:bg-yellow-50"
                          onClick={() => handleVerifyReceipt("flag")}
                        >
                          <AlertTriangle className="mr-2 h-4 w-4" />
                          Flag for CEO
                        </Button>
                        <Button
                          variant="destructive"
                          className="flex-1"
                          onClick={() => handleVerifyReceipt("reject")}
                        >
                          <X className="mr-2 h-4 w-4" />
                          Reject
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              {/* Navigation Footer */}
              <div className="flex items-center justify-between mt-6 p-4 border rounded-lg">
                <Button
                  variant="outline"
                  onClick={() => navigateReceipt("prev")}
                  disabled={currentIndex === 0}
                >
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Previous
                </Button>

                <div className="text-center">
                  <p className="text-sm font-medium">
                    Receipt {currentIndex + 1} of {receipts.length}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Use arrow keys to navigate
                  </p>
                </div>

                <Button
                  variant="outline"
                  onClick={() => navigateReceipt("next")}
                  disabled={currentIndex === receipts.length - 1}
                >
                  Next
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </TabsContent>
          )}
        </Tabs>

        {/* Fullscreen Image Dialog */}
        <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
          <DialogContent className="max-w-4xl h-[90vh]">
            <DialogHeader>
              <DialogTitle>Receipt Image - {currentReceipt?.order_id}</DialogTitle>
              <DialogDescription>
                Full-size receipt view
              </DialogDescription>
            </DialogHeader>
            <div className="flex-1 overflow-auto">
              {currentReceipt?.s3_url && (
                <img
                  src={currentReceipt.s3_url}
                  alt="Receipt Fullscreen"
                  className="w-full h-auto"
                />
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
    </VendorLayout>
  )
}
