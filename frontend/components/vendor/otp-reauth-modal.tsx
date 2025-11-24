"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import { toast } from "sonner"
import { Loader2, ShieldCheck } from "lucide-react"

interface OTPReauthModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  action: string // Description of the action requiring re-auth
  phone?: string // Vendor's phone number
}

/**
 * OTP Re-authentication Modal
 * Required for sensitive vendor actions per vendor frontend plan:
 * - Approving high-value receipts (>₦5,000 or configured threshold)
 * - Changing preferences
 * - Flagging receipts for CEO review
 */
export function OTPReauthModal({ isOpen, onClose, onSuccess, action, phone }: OTPReauthModalProps) {
  const [step, setStep] = useState<"REQUEST" | "VERIFY">("REQUEST")
  const [otp, setOtp] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleRequestOTP() {
    try {
      setLoading(true)
      await api.post("/auth/vendor/request-otp", {
        phone: phone || localStorage.getItem("vendor_phone")
      })
      toast.success("OTP sent to your device")
      setStep("VERIFY")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to send OTP")
    } finally {
      setLoading(false)
    }
  }

  async function handleVerifyOTP() {
    if (otp.length !== 8) {
      toast.error("Please enter the 8-character OTP")
      return
    }

    try {
      setLoading(true)
      const response = await api.post("/auth/vendor/verify-otp", {
        phone: phone || localStorage.getItem("vendor_phone"),
        otp
      })

      if (response.data.status === "success") {
        toast.success("Verified successfully")
        onSuccess()
        handleClose()
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Invalid OTP")
      setOtp("") // Clear OTP on failure
    } finally {
      setLoading(false)
    }
  }

  function handleClose() {
    setStep("REQUEST")
    setOtp("")
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            <DialogTitle>Verify Your Identity</DialogTitle>
          </div>
          <DialogDescription>
            This action requires re-authentication for security.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-lg bg-muted p-4">
            <p className="text-sm font-medium">Action:</p>
            <p className="text-sm text-muted-foreground">{action}</p>
          </div>

          {step === "REQUEST" ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Click below to receive an 8-character OTP via WhatsApp or SMS.
              </p>
              <Button
                onClick={handleRequestOTP}
                disabled={loading}
                className="w-full"
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Send OTP
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp">Enter 8-Character OTP</Label>
                <Input
                  id="otp"
                  type="text"
                  maxLength={8}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.toUpperCase())}
                  placeholder="B7#K9@P2"
                  className="font-mono text-center text-lg tracking-widest"
                  autoFocus
                />
                <p className="text-xs text-muted-foreground">
                  OTP contains letters, numbers, and symbols (!@#$%^&*)
                </p>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setStep("REQUEST")}
                  disabled={loading}
                  className="flex-1"
                >
                  Resend OTP
                </Button>
                <Button
                  onClick={handleVerifyOTP}
                  disabled={loading || otp.length !== 8}
                  className="flex-1"
                >
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Verify
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
