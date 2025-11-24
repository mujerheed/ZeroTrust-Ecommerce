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

const signupSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  phone: z.string().min(10, "Phone number must be at least 10 characters"),
  email: z.string().email("Invalid email address"),
})

const otpSchema = z.object({
  otp: z.string().length(6, "OTP must be 6 characters"),
})

export default function CEOSignupPage() {
  const [step, setStep] = useState<"DETAILS" | "OTP">("DETAILS")
  const [userId, setUserId] = useState("")
  const [otpValue, setOtpValue] = useState("")
  const router = useRouter()

  const signupForm = useForm<z.infer<typeof signupSchema>>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      name: "",
      phone: "",
      email: "",
    },
  })

  const otpForm = useForm<z.infer<typeof otpSchema>>({
    resolver: zodResolver(otpSchema),
    defaultValues: {
      otp: "",
    },
    mode: "onChange",
  })

  async function onSignupSubmit(values: z.infer<typeof signupSchema>) {
    try {
      const response = await api.post("/auth/ceo/register", values)
      
      const { ceo_id } = response.data.data
      setUserId(ceo_id)
      setStep("OTP")
      toast.success("Account created. OTP sent to your phone/email.")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Registration failed")
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
      toast.success("Signup successful")
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
      title="CEO Signup"
      description="Create your TrustGuard Business Account"
      backButton={
        step === "DETAILS" 
          ? { label: "Already have an account? Login", href: "/ceo/login" }
          : { label: "Back to Details", onClick: () => setStep("DETAILS") }
      }
    >
      {step === "DETAILS" ? (
        <Form {...signupForm}>
          <form onSubmit={signupForm.handleSubmit(onSignupSubmit)} className="space-y-4">
            <FormField
              control={signupForm.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full Name</FormLabel>
                  <FormControl>
                    <Input placeholder="John Doe" {...field} className="h-11" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={signupForm.control}
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
            <FormField
              control={signupForm.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email Address</FormLabel>
                  <FormControl>
                    <Input placeholder="john@example.com" {...field} className="h-11" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full h-11" disabled={signupForm.formState.isSubmitting}>
              {signupForm.formState.isSubmitting ? "Creating Account..." : "Create Account"}
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
                        length={6}
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
                {otpForm.formState.isSubmitting ? "Verifying..." : "Verify & Complete Signup"}
              </Button>
            </div>
          </form>
        </Form>
      )}
    </AuthWrapper>
  )
}
