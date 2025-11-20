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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"

const phoneSchema = z.object({
  phone: z.string().min(10, "Phone number must be at least 10 characters"),
})

const otpSchema = z.object({
  otp: z.string().length(8, "OTP must be 8 characters"),
})

export default function VendorLoginPage() {
  const [step, setStep] = useState<"PHONE" | "OTP">("PHONE")
  const [userId, setUserId] = useState("")
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
  })

  async function onPhoneSubmit(values: z.infer<typeof phoneSchema>) {
    try {
      const response = await api.post("/auth/vendor/login", {
        phone: values.phone,
      })
      
      const { vendor_id } = response.data.data
      setUserId(vendor_id)
      setStep("OTP")
      toast.success("OTP sent to your phone")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to send OTP")
    }
  }

  async function onOtpSubmit(values: z.infer<typeof otpSchema>) {
    try {
      const response = await api.post("/auth/verify-otp", {
        user_id: userId,
        otp: values.otp,
      })
      
      const { token, role } = response.data.data
      
      if (role !== "Vendor") {
        toast.error("Unauthorized: You are not a vendor")
        return
      }

      setToken(token)
      toast.success("Login successful")
      router.push("/vendor/dashboard")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Invalid OTP or Login Failed")
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle>Vendor Login</CardTitle>
          <CardDescription>Access your TrustGuard Vendor Dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          {step === "PHONE" ? (
            <Form {...phoneForm}>
              <form onSubmit={phoneForm.handleSubmit(onPhoneSubmit)} className="space-y-8">
                <FormField
                  control={phoneForm.control}
                  name="phone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Phone Number</FormLabel>
                      <FormControl>
                        <Input placeholder="+234..." {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full">Send OTP</Button>
              </form>
            </Form>
          ) : (
            <Form {...otpForm}>
              <form onSubmit={otpForm.handleSubmit(onOtpSubmit)} className="space-y-8">
                <FormField
                  control={otpForm.control}
                  name="otp"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Enter OTP</FormLabel>
                      <FormControl>
                        <Input placeholder="8-character OTP" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full">Verify & Login</Button>
                <Button variant="ghost" className="w-full" onClick={() => setStep("PHONE")}>
                  Back to Phone
                </Button>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
