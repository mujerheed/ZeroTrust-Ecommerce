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
      toast.success("Signup successful")
      router.push("/ceo/dashboard")
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Invalid OTP or Verification Failed")
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-[400px]">
        <CardHeader>
          <CardTitle>CEO Signup</CardTitle>
          <CardDescription>Create your TrustGuard Business Account</CardDescription>
        </CardHeader>
        <CardContent>
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
                        <Input placeholder="Ada Ogunleye" {...field} />
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
                        <Input placeholder="+234..." {...field} />
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
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input placeholder="ada@fashion.com" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full">Sign Up</Button>
                <div className="text-center text-sm">
                  Already have an account? <Link href="/ceo/login" className="underline">Login</Link>
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
                <Button variant="ghost" className="w-full" onClick={() => setStep("DETAILS")}>
                  Back to Details
                </Button>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
