"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { toast } from "sonner"
import { Settings, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface PreferencesData {
  auto_approve_threshold: number // in kobo
  textract_enabled: boolean
  updated_at: number | null
}

interface PreferencesModalProps {
  trigger?: React.ReactNode
  className?: string
}

export function PreferencesModal({ trigger, className }: PreferencesModalProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [preferences, setPreferences] = useState<PreferencesData>({
    auto_approve_threshold: 0,
    textract_enabled: true,
    updated_at: null,
  })

  // Convert kobo to naira for display
  const [displayAmount, setDisplayAmount] = useState("0")

  useEffect(() => {
    if (open) {
      fetchPreferences()
    }
  }, [open])

  useEffect(() => {
    // Update display amount when preferences change
    setDisplayAmount((preferences.auto_approve_threshold / 100).toFixed(2))
  }, [preferences.auto_approve_threshold])

  async function fetchPreferences() {
    try {
      setLoading(true)
      const response = await api.get("/vendor/preferences")
      const data = response.data.data
      setPreferences(data)
    } catch (error: any) {
      // If preferences don't exist yet, use defaults
      if (error.response?.status === 404 || error.response?.status === 500) {
        setPreferences({
          auto_approve_threshold: 0,
          textract_enabled: true,
          updated_at: null,
        })
      } else {
        toast.error("Failed to load preferences")
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    try {
      setSaving(true)

      // Convert naira to kobo
      const amountInKobo = Math.round(parseFloat(displayAmount) * 100)

      // Validate
      if (amountInKobo < 0) {
        toast.error("Amount cannot be negative")
        return
      }

      if (amountInKobo > 100000000) {
        // ₦1,000,000 max
        toast.error("Maximum auto-approve threshold is ₦1,000,000")
        return
      }

      await api.put("/vendor/preferences", {
        auto_approve_threshold: amountInKobo,
        textract_enabled: preferences.textract_enabled,
      })

      toast.success("Preferences saved successfully")
      setOpen(false)
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to save preferences")
    } finally {
      setSaving(false)
    }
  }

  function handleAmountChange(value: string) {
    // Allow only numbers and decimal point
    const sanitized = value.replace(/[^\d.]/g, "")
    
    // Prevent multiple decimal points
    const parts = sanitized.split(".")
    if (parts.length > 2) return
    
    // Limit to 2 decimal places
    if (parts[1] && parts[1].length > 2) return

    setDisplayAmount(sanitized)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button
            variant="outline"
            size="icon"
            className={cn(
              "fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-all",
              className
            )}
          >
            <Settings className="h-6 w-6" />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Vendor Preferences</DialogTitle>
          <DialogDescription>
            Configure your receipt verification and automation settings
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-6 py-4">
            {/* Auto-Approve Threshold */}
            <div className="space-y-3">
              <div>
                <Label htmlFor="threshold" className="text-base font-medium">
                  Auto-Approve Threshold
                </Label>
                <p className="text-sm text-muted-foreground mt-1">
                  Receipts below this amount will be automatically approved without manual review
                </p>
              </div>

              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    ₦
                  </span>
                  <Input
                    id="threshold"
                    type="text"
                    value={displayAmount}
                    onChange={(e) => handleAmountChange(e.target.value)}
                    placeholder="0.00"
                    className="pl-7"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {displayAmount === "0" ? "Disabled (all receipts require review)" : "Enabled"}
                </span>
                <span className="text-muted-foreground">
                  Max: ₦1,000,000
                </span>
              </div>

              {/* Quick Presets */}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setDisplayAmount("0")}
                >
                  Disable
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setDisplayAmount("5000")}
                >
                  ₦5,000
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setDisplayAmount("10000")}
                >
                  ₦10,000
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setDisplayAmount("50000")}
                >
                  ₦50,000
                </Button>
              </div>
            </div>

            {/* Textract OCR */}
            <div className="space-y-3 pt-4 border-t">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="textract" className="text-base font-medium">
                    Textract OCR Verification
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Use AI-powered OCR to automatically extract and verify receipt details
                  </p>
                </div>
                <Switch
                  id="textract"
                  checked={preferences.textract_enabled}
                  onCheckedChange={(checked) =>
                    setPreferences({ ...preferences, textract_enabled: checked })
                  }
                />
              </div>

              {preferences.textract_enabled && (
                <div className="bg-blue-50 dark:bg-blue-950 p-3 rounded-lg">
                  <p className="text-xs text-blue-900 dark:text-blue-100">
                    <strong>Enabled:</strong> Receipt images will be processed by AWS Textract to
                    extract amount, date, bank details, and reference numbers with confidence scores.
                  </p>
                </div>
              )}
            </div>

            {/* Last Updated */}
            {preferences.updated_at && (
              <div className="text-xs text-muted-foreground text-center pt-2 border-t">
                Last updated: {new Date(preferences.updated_at * 1000).toLocaleString()}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading || saving}>
            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
