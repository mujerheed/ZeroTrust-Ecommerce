"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useRouter } from "next/navigation"
import { api, setToken } from "@/lib/api"
import { initSession } from "@/lib/session"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import { AuthWrapper } from "@/components/auth-wrapper"
import { OTPInput } from "@/components/ui/otp-input"

const phoneSchema = z.object({
  phone: z.string().min(10, "Phone number must be at least 10 characters"),
})

const otpSchema = z.object({
  otp: z.string().length(8, "OTP must be 8 characters"),
})

export default function VendorLoginPage() {
  const [step, setStep] = useState<"PHONE" | "OTP">("PHONE")
  const [userId, setUserId] = useState("")
  const [otpValue, setOtpValue] = useState("")
  const router = useRouter()

  const phoneForm = useForm<z.infer<typeof phoneSchema>>({
    resolver: zodResolver(phoneSchema),
    defaultValues: {
      phone: "",
    },
  })

  const otpForm = useForm<z.infer<typeof otpSchema>>({
    resolver: zodResolver(otpSchema),
    defaultValues: {
      otp: "",
    },
    mode: "onSubmit",
  })

  async function onPhoneSubmit(values: z.infer<typeof phoneSchema>) {
    try {
      console.log("🔐 Requesting vendor OTP for phone:", values.phone)
      const response = await api.post("/auth/vendor/login", {
        phone: values.phone,
      })
      
      console.log("✅ OTP request response:", response.data)
      
      const { vendor_id, dev_otp } = response.data.data
      setUserId(vendor_id)
      setStep("OTP")
      
      // In development, show the OTP in console
      if (dev_otp) {
        console.log("🔑 DEV OTP:", dev_otp)
        toast.success(`OTP sent! (Dev: ${dev_otp})`, { duration: 10000 })
      } else {
        toast.success("OTP sent to your phone")
      }
    } catch (error: any) {
      console.error("❌ OTP request failed:", error)
      console.error("Error response:", error.response?.data)
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || "Failed to send OTP"
      toast.error(errorMsg)
    }
  }

  async function onOtpSubmit(values: z.infer<typeof otpSchema>) {
    try {
      // Use the passed value, or fall back to otpValue state
      const otpToVerify = values.otp || otpValue
      
      if (!otpToVerify || otpToVerify.length !== 8) {
        toast.error("Please enter a valid 8-character OTP")
        return
      }

      const response = await api.post("/auth/verify-otp", {
        user_id: userId,
        otp: otpToVerify,
      })
      
      const { token, role } = response.data.data
      
      if (role !== "Vendor") {
        toast.error("Unauthorized: You are not a vendor")
        return
      }

      setToken(token, 'vendor')
      initSession('vendor') // Initialize 60-minute session timer for vendor
      toast.success("Login successful")
      router.push("/vendor/dashboard")
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.response?.data?.message || "Invalid OTP")
    }
  }

  // Auto-submit when OTP is complete
  const handleOtpChange = (value: string) => {
    setOtpValue(value)
    otpForm.setValue("otp", value, { shouldValidate: false })
    
    // Auto-submit when 8 characters are entered
    if (value.length === 8) {
      setTimeout(() => {
        onOtpSubmit({ otp: value })
      }, 100)
    }
  }

  return (
    <AuthWrapper
      title="Vendor Portal"
      description={step === "PHONE" 
        ? "Enter your phone number to access your dashboard" 
        : "Enter the 8-digit code sent to your device"}
      backButton={
        step === "PHONE" 
          ? { label: "Back to Home", href: "/" }
          : { label: "Back to Phone", onClick: () => setStep("PHONE") }
      }
    >
      {step === "PHONE" ? (
        <Form {...phoneForm}>
          <form onSubmit={phoneForm.handleSubmit(onPhoneSubmit)} className="space-y-4">
            <FormField
              control={phoneForm.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phone Number</FormLabel>
                  <FormControl>
                    <Input placeholder="+234..." {...field} className="h-11" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full h-11" disabled={phoneForm.formState.isSubmitting}>
              {phoneForm.formState.isSubmitting ? "Sending..." : "Send OTP"}
            </Button>
          </form>
        </Form>
      ) : (
        <Form {...otpForm}>
          <form onSubmit={otpForm.handleSubmit(onOtpSubmit)} className="space-y-6">
            <FormField
              control={otpForm.control}
              name="otp"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>One-Time Password</FormLabel>
                  <FormControl>
                    <div className="flex justify-center">
                      <OTPInput
                        length={8}
                        value={otpValue}
                        onChange={handleOtpChange}
                        masked={true}
                      />
                    </div>
                  </FormControl>
                  <FormMessage className="text-center" />
                </FormItem>
              )}
            />
            <div className="space-y-2">
              <Button type="submit" className="w-full h-11" disabled={otpForm.formState.isSubmitting}>
                {otpForm.formState.isSubmitting ? "Verifying..." : "Verify & Login"}
              </Button>
            </div>
          </form>
        </Form>
      )}
    </AuthWrapper>
  )
}
