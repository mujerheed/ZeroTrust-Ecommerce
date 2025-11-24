"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle, ShieldCheck } from "lucide-react"
import Link from "next/link"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

interface Escalation {
  request_id: string
  order_id: string
  vendor_id: string
  reason: string
  status: string
  created_at: string
  receipt_url?: string
  amount?: number
  buyer_id?: string
}

export default function EscalationReviewPage() {
  const params = useParams()
  const router = useRouter()
  const [escalation, setEscalation] = useState<Escalation | null>(null)
  const [loading, setLoading] = useState(true)
  const [otp, setOtp] = useState("")
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false)
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState("")

  useEffect(() => {
    if (params.id) {
      fetchEscalation()
    }
  }, [params.id])

  async function fetchEscalation() {
    try {
      const response = await api.get(`/ceo/escalations/${params.id}`)
      setEscalation(response.data.data)
    } catch (error: any) {
      toast.error("Failed to load escalation details")
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove() {
    try {
      await api.post(`/ceo/escalations/${params.id}/approve`, {
        otp: otp
      })
      toast.success("Transaction approved successfully")
      setIsApproveDialogOpen(false)
      router.push("/ceo/dashboard")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to approve transaction")
    }
  }

  async function handleReject() {
    try {
      await api.post(`/ceo/escalations/${params.id}/reject`, {
        reason: rejectReason
      })
      toast.success("Transaction rejected")
      setIsRejectDialogOpen(false)
      router.push("/ceo/dashboard")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to reject transaction")
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!escalation) {
    return <div className="flex items-center justify-center min-h-screen">Escalation not found</div>
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex items-center gap-4">
          <Link href="/ceo/dashboard">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Review Escalation</h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left Column: Details */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  Escalation Details
                </CardTitle>
                <CardDescription>
                  This transaction requires your approval.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">Reason</Label>
                    <p className="font-medium">{escalation.reason}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Status</Label>
                    <Badge variant={escalation.status === 'pending' ? 'outline' : 'default'}>
                      {escalation.status}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Amount</Label>
                    <p className="font-medium text-lg">₦{escalation.amount?.toLocaleString() || 'N/A'}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Date</Label>
                    <p className="font-medium">{new Date(escalation.created_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Vendor ID</Label>
                    <p className="font-mono text-sm">{escalation.vendor_id}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Order ID</Label>
                    <p className="font-mono text-sm">{escalation.order_id}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Dialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="destructive" className="flex-1">
                    <XCircle className="mr-2 h-4 w-4" /> Reject
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Reject Transaction</DialogTitle>
                    <DialogDescription>
                      Please provide a reason for rejecting this transaction.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4">
                    <Label>Rejection Reason</Label>
                    <Input 
                      placeholder="e.g., Invalid receipt, Suspicious activity" 
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                    />
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsRejectDialogOpen(false)}>Cancel</Button>
                    <Button variant="destructive" onClick={handleReject}>Confirm Reject</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="flex-1 bg-green-600 hover:bg-green-700">
                    <CheckCircle className="mr-2 h-4 w-4" /> Approve
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Approve Transaction</DialogTitle>
                    <DialogDescription>
                      Enter your CEO OTP to authorize this high-value or flagged transaction.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4 space-y-4">
                    <div className="bg-yellow-50 p-4 rounded-md flex items-start gap-3">
                      <ShieldCheck className="h-5 w-5 text-yellow-600 mt-0.5" />
                      <p className="text-sm text-yellow-800">
                        This action is irreversible and will be logged in the immutable audit trail.
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label>Enter CEO OTP</Label>
                      <Input 
                        placeholder="Enter 6-digit OTP" 
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                        className="text-center text-lg tracking-widest"
                      />
                      <p className="text-xs text-muted-foreground text-center">
                        Check your registered device for the OTP.
                      </p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsApproveDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleApprove} className="bg-green-600 hover:bg-green-700">
                      Confirm Approval
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Right Column: Receipt Preview */}
          <Card className="h-fit">
            <CardHeader>
              <CardTitle>Receipt Evidence</CardTitle>
            </CardHeader>
            <CardContent>
              {escalation.receipt_url ? (
                <div className="border rounded-lg overflow-hidden bg-gray-100">
                  {/* In a real app, use Next.js Image with proper domains config */}
                  <img 
                    src={escalation.receipt_url} 
                    alt="Receipt" 
                    className="w-full h-auto object-contain max-h-[500px]"
                  />
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center bg-gray-100 rounded-lg text-muted-foreground">
                  No receipt image available
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
