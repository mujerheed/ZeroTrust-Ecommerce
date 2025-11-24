"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useRouter } from "next/navigation"
import { api, setToken } from "@/lib/api"
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
import Link from "next/link"
import { AuthWrapper } from "@/components/auth-wrapper"
import { OTPInput } from "@/components/ui/otp-input"
import { initSession } from "@/lib/session"

const contactSchema = z.object({
  contact: z.string().min(3, "Enter a valid email or phone number"),
})

const otpSchema = z.object({
  otp: z.string().length(6, "OTP must be 6 characters"),
})

export default function CEOLoginPage() {
  const [step, setStep] = useState<"CONTACT" | "OTP">("CONTACT")
  const [userId, setUserId] = useState("")
  const [otpValue, setOtpValue] = useState("")
  const router = useRouter()

  const contactForm = useForm<z.infer<typeof contactSchema>>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      contact: "",
    },
  })

  const otpForm = useForm<z.infer<typeof otpSchema>>({
    resolver: zodResolver(otpSchema),
    defaultValues: {
      otp: "",
    },
    mode: "onSubmit",
  })

  async function onContactSubmit(values: z.infer<typeof contactSchema>) {
    try {
      console.log("🔐 Requesting CEO OTP for contact:", values.contact)
      const response = await api.post("/auth/ceo/login", {
        contact: values.contact,
      })
      
      console.log("✅ OTP request response:", response.data)
      
      const { ceo_id, dev_otp } = response.data.data
      setUserId(ceo_id)
      setStep("OTP")
      
      // In development, show the OTP in console
      if (dev_otp) {
        console.log("🔑 DEV OTP:", dev_otp)
        toast.success(`OTP sent! (Dev: ${dev_otp})`, { duration: 10000 })
      } else {
        toast.success("OTP sent to your contact method")
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
      
      if (!otpToVerify || otpToVerify.length !== 6) {
        toast.error("Please enter a valid 6-character OTP")
        return
      }

      const response = await api.post("/auth/verify-otp", {
        user_id: userId,
        otp: otpToVerify,
      })
      
      const { token, role } = response.data.data
      
      if (role !== "CEO") {
        toast.error("Unauthorized: You are not a CEO")
        return
      }

      setToken(token, 'ceo')
      initSession('ceo') // Initialize 60-minute session timer for CEO
      toast.success("Login successful")
      router.push("/ceo/dashboard")
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.response?.data?.message || "Invalid OTP")
    }
  }

  // Auto-submit when OTP is complete
  const handleOtpChange = (value: string) => {
    setOtpValue(value)
    otpForm.setValue("otp", value, { shouldValidate: false })
    
    // Auto-submit when 6 characters are entered
    if (value.length === 6) {
      setTimeout(() => {
        onOtpSubmit({ otp: value })
      }, 100)
    }
  }

  return (
    <AuthWrapper
      title="CEO Portal"
      description={step === "CONTACT" ? "Sign in to manage your organization" : "Enter the 6-digit code sent to you"}
      backButton={
        step === "CONTACT" 
          ? { label: "Don't have an account? Sign up", href: "/ceo/signup" }
          : { label: "Back to Contact", onClick: () => setStep("CONTACT") }
      }
    >
      {step === "CONTACT" ? (
        <Form {...contactForm}>
          <form onSubmit={contactForm.handleSubmit(onContactSubmit)} className="space-y-4">
            <FormField
              control={contactForm.control}
              name="contact"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email or Phone</FormLabel>
                  <FormControl>
                    <Input placeholder="admin@example.com or +234..." {...field} className="h-11" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full h-11" disabled={contactForm.formState.isSubmitting}>
              {contactForm.formState.isSubmitting ? "Sending..." : "Send OTP"}
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
                  <div className="flex justify-center">
                    <OTPInput
                      length={6}
                      value={otpValue}
                      onChange={handleOtpChange}
                      masked={true}
                    />
                  </div>
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
