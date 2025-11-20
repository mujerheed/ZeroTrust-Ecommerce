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
import Link from "next/link"

const contactSchema = z.object({
  contact: z.string().min(3, "Enter a valid email or phone number"),
})

const otpSchema = z.object({
  otp: z.string().length(6, "OTP must be 6 characters"),
})

export default function CEOLoginPage() {
  const [step, setStep] = useState<"CONTACT" | "OTP">("CONTACT")
  const [userId, setUserId] = useState("")
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
  })

  async function onContactSubmit(values: z.infer<typeof contactSchema>) {
    try {
      const response = await api.post("/auth/ceo/login", {
        contact: values.contact,
      })
      
      const { ceo_id } = response.data.data
      setUserId(ceo_id)
      setStep("OTP")
      toast.success("OTP sent to your contact method")
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
      
      if (role !== "CEO") {
        toast.error("Unauthorized: You are not a CEO")
        return
      }

      setToken(token)
      toast.success("Login successful")
      router.push("/ceo/dashboard")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Invalid OTP or Login Failed")
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle>CEO Login</CardTitle>
          <CardDescription>Access your TrustGuard CEO Dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          {step === "CONTACT" ? (
            <Form {...contactForm}>
              <form onSubmit={contactForm.handleSubmit(onContactSubmit)} className="space-y-8">
                <FormField
                  control={contactForm.control}
                  name="contact"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email or Phone</FormLabel>
                      <FormControl>
                        <Input placeholder="admin@example.com or +234..." {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full">Send OTP</Button>
                <div className="text-center text-sm">
                  Don't have an account? <Link href="/ceo/signup" className="underline">Sign up</Link>
                </div>
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
                        <Input placeholder="6-character OTP" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full">Verify & Login</Button>
                <Button variant="ghost" className="w-full" onClick={() => setStep("CONTACT")}>
                  Back to Contact
                </Button>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
