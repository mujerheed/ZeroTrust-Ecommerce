"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { ArrowLeft, CheckCircle, AlertTriangle, Download, MessageSquare } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import Link from "next/link"

interface OrderDetail {
  order: {
    order_id: string
    buyer_id: string
    total_amount: number
    status: string
    created_at: string
    items: Array<{
      name: string
      quantity: number
      unit_price: number
    }>
    negotiation_history?: Array<{
      sender: string
      message: string
      timestamp: string
    }>
  }
  buyer: {
    buyer_name: string
    buyer_phone: string
    delivery_address: string
  }
  receipt?: {
    receipt_url: string
    uploaded_at: string
    metadata: {
      amount: number
      checksum: string
    }
    verification_status?: string
  }
}

export default function OrderDetailPage() {
  const [data, setData] = useState<OrderDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [notes, setNotes] = useState("")
  const params = useParams()
  const router = useRouter()

  useEffect(() => {
    if (params.id) {
      fetchOrderDetails(params.id as string)
    }
  }, [params.id])

  async function fetchOrderDetails(orderId: string) {
    try {
      const response = await api.get(`/vendor/orders/${orderId}`)
      setData(response.data.data)
    } catch (error: any) {
      toast.error("Failed to load order details")
      router.push("/vendor/dashboard")
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify(status: 'verified' | 'flagged') {
    if (!data) return

    try {
      await api.post(`/vendor/orders/${data.order.order_id}/verify`, {
        verification_status: status,
        notes: notes
      })
      toast.success(status === 'verified' ? "Receipt verified successfully" : "Receipt flagged")
      fetchOrderDetails(data.order.order_id) // Refresh data
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Action failed")
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!data) {
    return <div className="flex items-center justify-center min-h-screen">Order not found</div>
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex items-center gap-4">
          <Link href="/vendor/dashboard">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-foreground">Order {data.order.order_id.substring(0, 8)}...</h1>
          <Badge variant={
            data.order.status === 'COMPLETED' ? 'default' : 
            data.order.status === 'PENDING' ? 'secondary' : 'destructive'
          }>
            {data.order.status}
          </Badge>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* Left Column: Order Info & Chat */}
          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>Order Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Buyer</p>
                    <p className="font-medium">{data.buyer.buyer_name || data.order.buyer_id}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Phone</p>
                    <p className="font-medium">{data.buyer.buyer_phone}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-muted-foreground">Delivery Address</p>
                    <p className="font-medium">{data.buyer.delivery_address || "Not provided"}</p>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <p className="font-medium mb-2">Items</p>
                  <div className="space-y-2">
                    {data.order.items?.map((item, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span>{item.quantity}x {item.name}</span>
                        <span>₦{(item.unit_price * item.quantity).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between font-bold mt-4 pt-4 border-t">
                    <span>Total</span>
                    <span>₦{data.order.total_amount.toLocaleString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Negotiation History (Chat) */}
            <Card className="h-[400px] flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" /> Negotiation History
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto space-y-4">
                {data.order.negotiation_history?.map((msg, i) => (
                  <div key={i} className={`flex flex-col ${msg.sender === 'vendor' ? 'items-end' : 'items-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-3 ${
                      msg.sender === 'vendor' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'
                    }`}>
                      <p className="text-sm">{msg.message}</p>
                    </div>
                    <span className="text-xs text-muted-foreground mt-1">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
                {!data.order.negotiation_history?.length && (
                  <div className="text-center text-muted-foreground py-8">No messages yet</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Receipt Verification */}
          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>Receipt Verification</CardTitle>
                <CardDescription>Verify the payment proof uploaded by the buyer.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {data.receipt ? (
                  <>
                    <div className="aspect-video relative bg-gray-100 rounded-lg overflow-hidden border">
                      {/* In a real app, use Next.js Image with a signed URL */}
                      <img 
                        src={data.receipt.receipt_url} 
                        alt="Receipt" 
                        className="object-contain w-full h-full"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-muted-foreground">Claimed Amount</p>
                        <p className="font-medium">₦{data.receipt.metadata.amount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Uploaded At</p>
                        <p className="font-medium">{new Date(data.receipt.uploaded_at).toLocaleString()}</p>
                      </div>
                      <div className="col-span-2">
                        <p className="text-muted-foreground">Checksum</p>
                        <p className="font-mono text-xs truncate">{data.receipt.metadata.checksum}</p>
                      </div>
                    </div>

                    {data.order.status === 'PENDING' && (
                      <div className="flex gap-4">
                        <Button 
                          className="flex-1 bg-green-600 hover:bg-green-700"
                          onClick={() => handleVerify('verified')}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" /> Approve
                        </Button>
                        
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="destructive" className="flex-1">
                              <AlertTriangle className="mr-2 h-4 w-4" /> Flag
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Flag Receipt</DialogTitle>
                              <DialogDescription>
                                Why are you flagging this receipt? This will notify the CEO.
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                              <div className="space-y-2">
                                <Label>Reason / Notes</Label>
                                <Textarea 
                                  placeholder="e.g., Amount mismatch, blurry image..." 
                                  value={notes}
                                  onChange={(e) => setNotes(e.target.value)}
                                />
                              </div>
                            </div>
                            <DialogFooter>
                              <Button variant="outline" onClick={() => setNotes("")}>Cancel</Button>
                              <Button variant="destructive" onClick={() => handleVerify('flagged')}>
                                Confirm Flag
                              </Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12 border-2 border-dashed rounded-lg">
                    <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                    <p className="text-muted-foreground">No receipt uploaded yet</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Link href={`/api/orders/${data.order.order_id}/download-pdf`} target="_blank">
                  <Button variant="outline" className="w-full">
                    <Download className="mr-2 h-4 w-4" /> Download Invoice PDF
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
