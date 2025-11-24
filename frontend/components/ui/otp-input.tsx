"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface OTPInputProps {
  length: number
  value: string
  onChange: (value: string) => void
  className?: string
  masked?: boolean
}

export function OTPInput({ length, value, onChange, className, masked = false }: OTPInputProps) {
  const inputRefs = React.useRef<(HTMLInputElement | null)[]>([])

  const handleChange = (index: number, inputValue: string) => {
    // Only allow single character
    const newValue = inputValue.slice(-1)
    
    const newOTP = value.split("")
    while (newOTP.length < length) {
      newOTP.push("")
    }
    newOTP[index] = newValue
    
    const result = newOTP.join("")
    onChange(result)

    // Auto-focus next input
    if (newValue && index < length - 1) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (!value[index] && index > 0) {
        // If current box is empty, go to previous box
        inputRefs.current[index - 1]?.focus()
      } else {
        // Clear current box
        const newOTP = value.split("")
        newOTP[index] = ""
        onChange(newOTP.join(""))
      }
    } else if (e.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === "ArrowRight" && index < length - 1) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const rawData = e.clipboardData.getData("text/plain")
    
    // Filter to only keep alphanumeric characters and allowed special chars
    const pastedData = rawData.replace(/[^0-9a-zA-Z!@#$%^&*]/g, "").slice(0, length)
    
    onChange(pastedData)
    
    // Focus the next empty input or the last one
    const nextIndex = Math.min(pastedData.length, length - 1)
    inputRefs.current[nextIndex]?.focus()
  }

  return (
    <div className={cn("flex gap-1.5 items-center justify-center max-w-full", className)}>
      {Array.from({ length }).map((_, index) => {
        const charValue = value[index] || ""
        // Show separator: 
        // - For 8-char OTP: after 4th box (index 3)
        // - For 6-char OTP: after 3rd box (index 2)
        const showSeparator = (length === 8 && index === 3) || (length === 6 && index === 2)
        
        return (
          <React.Fragment key={index}>
            <input
              ref={(el) => {
                inputRefs.current[index] = el
              }}
              type={masked ? "password" : "text"}
              inputMode="text"
              autoComplete="off"
              maxLength={1}
              value={charValue}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              onPaste={handlePaste}
              className={cn(
                "h-11 w-10 text-center text-xl font-bold",
                "border-2 border-gray-300 rounded-md",
                "focus:border-blue-500 focus:ring-1 focus:ring-blue-200 focus:outline-none",
                "transition-all",
                "bg-white text-gray-900",
                "placeholder:text-gray-400"
              )}
              style={{
                color: '#000000',
                backgroundColor: '#ffffff'
              }}
            />
            {showSeparator && (
              <div className="w-2 h-0.5 bg-gray-400 mx-0.5" />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}
