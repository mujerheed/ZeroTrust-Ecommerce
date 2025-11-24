"use client"

import { Suspense, useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
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
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { toast } from "sonner"
import { CEOLayout } from "@/components/ceo/CEOLayout"
import { 
  ArrowLeft, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  ShieldAlert,
  TrendingUp,
  Eye
} from "lucide-react"
import Link from "next/link"
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp"
import { ReceiptPreview } from "@/components/ceo/ReceiptPreview"

interface ApprovalItem {
  order_id: string
  buyer_id: string
  vendor_id: string
  vendor_name?: string
  total_amount: number
  order_status: string
  flagged_reason?: string
  escalation_reason: string
  created_at: string
}

interface ApprovalsData {
  pending_approvals: ApprovalItem[]
  total_pending: number
  high_value_count: number
  flagged_count: number
}

function CEOApprovalsPageContent() {
  const [approvalsData, setApprovalsData] = useState<ApprovalsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedOrder, setSelectedOrder] = useState<ApprovalItem | null>(null)
  const [actionType, setActionType] = useState<"approve" | "reject" | null>(null)
  const [otp, setOtp] = useState("")
  const [notes, setNotes] = useState("")
  const [rejectReason, setRejectReason] = useState("")
  const [otpRequested, setOtpRequested] = useState(false)
  const [requestingOtp, setRequestingOtp] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [devOtp, setDevOtp] = useState<string>("")
  const [receiptPreviewOrder, setReceiptPreviewOrder] = useState<string | null>(null)
  
  const router = useRouter()
  const searchParams = useSearchParams()
  const highlightOrderId = searchParams.get("order")

  useEffect(() => {
    fetchApprovals()
  }, [])

  async function fetchApprovals() {
    setLoading(true)
    try {
      const response = await api.get("/ceo/approvals")
      setApprovalsData(response.data.data)
    } catch (error: any) {
      toast.error("Failed to load approvals")
      if (error.response?.status === 401) {
        router.push("/ceo/login")
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleRequestOtp(order: ApprovalItem) {
    setRequestingOtp(true)
    try {
      const response = await api.post("/ceo/approvals/request-otp", null, {
        params: { order_id: order.order_id }
      })
      
      // In development, the OTP is returned in the response
      if (response.data.data?.dev_otp) {
        setDevOtp(response.data.data.dev_otp)
        toast.success(`OTP sent! (Dev: ${response.data.data.dev_otp})`)
      } else {
        toast.success("OTP sent to your registered contact")
      }
      
      setOtpRequested(true)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to request OTP")
    } finally {
      setRequestingOtp(false)
    }
  }

  async function handleApprove() {
    if (!selectedOrder) return
    
    if (!otpRequested) {
      await handleRequestOtp(selectedOrder)
      return
    }

    if (!otp || otp.length !== 6) {
      toast.error("Please enter the 6-digit OTP")
      return
    }

    setSubmitting(true)
    try {
      await api.patch(`/ceo/approvals/${selectedOrder.order_id}/approve`, {
        otp,
        notes: notes || undefined
      })
      
      toast.success("Order approved successfully!")
      handleCloseDialog()
      fetchApprovals()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to approve order")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleReject() {
    if (!selectedOrder) return

    if (!rejectReason.trim()) {
      toast.error("Please provide a reason for rejection")
      return
    }

    setSubmitting(true)
    try {
      await api.patch(`/ceo/approvals/${selectedOrder.order_id}/reject`, {
        reason: rejectReason
      })
      
      toast.success("Order rejected successfully!")
      handleCloseDialog()
      fetchApprovals()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to reject order")
    } finally {
      setSubmitting(false)
    }
  }

  function handleOpenApproveDialog(order: ApprovalItem) {
    setSelectedOrder(order)
    setActionType("approve")
    setOtp("")
    setNotes("")
    setOtpRequested(false)
    setDevOtp("")
  }

  function handleOpenRejectDialog(order: ApprovalItem) {
    setSelectedOrder(order)
    setActionType("reject")
    setRejectReason("")
  }

  function handleCloseDialog() {
    setSelectedOrder(null)
    setActionType(null)
    setOtp("")
    setNotes("")
    setRejectReason("")
    setOtpRequested(false)
    setDevOtp("")
  }

  if (loading) {
    return (
      <CEOLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-muted-foreground">Loading approvals...</p>
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
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
              Approvals & Escalations
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Review high-value orders and flagged receipts
            </p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-l-4 border-l-orange-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
              <Clock className="h-5 w-5 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{approvalsData?.total_pending || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Require your attention
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">High-Value Orders</CardTitle>
              <TrendingUp className="h-5 w-5 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{approvalsData?.high_value_count || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                ≥ ₦1,000,000
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-red-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Flagged Receipts</CardTitle>
              <ShieldAlert className="h-5 w-5 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{approvalsData?.flagged_count || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Suspicious activity
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Pending Approvals Table */}
        <Card>
          <CardHeader>
            <CardTitle>Pending Approvals</CardTitle>
            <CardDescription>
              Orders requiring CEO authorization
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!approvalsData?.pending_approvals || approvalsData.pending_approvals.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <p className="text-lg font-semibold text-slate-600 dark:text-slate-400">
                  All caught up!
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-500 mt-1">
                  No pending approvals at the moment
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
                      <TableHead>Reason</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {approvalsData.pending_approvals.map((approval) => (
                      <TableRow 
                        key={approval.order_id}
                        className={highlightOrderId === approval.order_id ? "bg-yellow-50 dark:bg-yellow-900/20" : ""}
                      >
                        <TableCell className="font-mono text-sm">
                          {approval.order_id.substring(0, 8)}...
                        </TableCell>
                        <TableCell>{approval.buyer_id}</TableCell>
                        <TableCell>{approval.vendor_name || "Unknown"}</TableCell>
                        <TableCell className="font-semibold">
                          ₦{approval.total_amount.toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant={approval.escalation_reason === "high_value" ? "default" : "destructive"}>
                            {approval.escalation_reason === "high_value" ? "High Value" : "Flagged"}
                          </Badge>
                          {approval.flagged_reason && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {approval.flagged_reason}
                            </p>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(approval.created_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Link href={`/ceo/orders/${approval.order_id}`}>
                              <Button variant="ghost" size="sm" title="View Order Details">
                                <Eye className="h-4 w-4" />
                              </Button>
                            </Link>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => setReceiptPreviewOrder(approval.order_id)}
                              title="View Receipt"
                            >
                              📄
                            </Button>
                            <Button 
                              variant="default" 
                              size="sm"
                              onClick={() => handleOpenApproveDialog(approval)}
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Approve
                            </Button>
                            <Button 
                              variant="destructive" 
                              size="sm"
                              onClick={() => handleOpenRejectDialog(approval)}
                            >
                              <XCircle className="h-4 w-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Approve Dialog */}
        <Dialog open={actionType === "approve"} onOpenChange={(open) => !open && handleCloseDialog()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                Approve Order
              </DialogTitle>
              <DialogDescription>
                Order ID: <span className="font-mono">{selectedOrder?.order_id.substring(0, 16)}...</span>
                <br />
                Amount: <span className="font-bold">₦{selectedOrder?.total_amount.toLocaleString()}</span>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {!otpRequested ? (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    <AlertTriangle className="h-4 w-4 inline mr-2" />
                    This action requires OTP verification for security.
                  </p>
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label>Enter OTP</Label>
                    <div className="flex justify-center">
                      <InputOTP maxLength={6} value={otp} onChange={setOtp}>
                        <InputOTPGroup>
                          <InputOTPSlot index={0} />
                          <InputOTPSlot index={1} />
                          <InputOTPSlot index={2} />
                          <InputOTPSlot index={3} />
                          <InputOTPSlot index={4} />
                          <InputOTPSlot index={5} />
                        </InputOTPGroup>
                      </InputOTP>
                    </div>
                    {devOtp && (
                      <p className="text-xs text-center text-muted-foreground">
                        Development OTP: <span className="font-mono font-bold">{devOtp}</span>
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="notes">Notes (Optional)</Label>
                    <Textarea
                      id="notes"
                      placeholder="Add any notes about this approval..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                    />
                  </div>
                </>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleCloseDialog} disabled={submitting || requestingOtp}>
                Cancel
              </Button>
              <Button 
                onClick={handleApprove} 
                disabled={submitting || requestingOtp}
                className="bg-green-600 hover:bg-green-700"
              >
                {requestingOtp ? "Requesting OTP..." : submitting ? "Approving..." : otpRequested ? "Confirm Approval" : "Request OTP"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Reject Dialog */}
        <Dialog open={actionType === "reject"} onOpenChange={(open) => !open && handleCloseDialog()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-red-600">
                <XCircle className="h-5 w-5" />
                Reject Order
              </DialogTitle>
              <DialogDescription>
                Order ID: <span className="font-mono">{selectedOrder?.order_id.substring(0, 16)}...</span>
                <br />
                Amount: <span className="font-bold">₦{selectedOrder?.total_amount.toLocaleString()}</span>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="text-sm text-red-800 dark:text-red-200">
                  <AlertTriangle className="h-4 w-4 inline mr-2" />
                  Please provide a clear reason for rejection. This will be logged for audit.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="reason">Rejection Reason *</Label>
                <Textarea
                  id="reason"
                  placeholder="e.g., Receipt appears forged, Amount discrepancy, etc."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  rows={4}
                  required
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleCloseDialog} disabled={submitting}>
                Cancel
              </Button>
              <Button 
                variant="destructive"
                onClick={handleReject} 
                disabled={submitting || !rejectReason.trim()}
              >
                {submitting ? "Rejecting..." : "Confirm Rejection"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Receipt Preview Modal */}
        <ReceiptPreview 
          orderId={receiptPreviewOrder || ""}
          isOpen={!!receiptPreviewOrder}
          onClose={() => setReceiptPreviewOrder(null)}
        />
      </div>
    </CEOLayout>
  )
}

// Wrap with Suspense to handle useSearchParams
export default function CEOApprovalsPage() {
  return (
    <Suspense fallback={
      <CEOLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading approvals...</p>
          </div>
        </div>
      </CEOLayout>
    }>
      <CEOApprovalsPageContent />
    </Suspense>
  )
}
