"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { toast } from "sonner"
import { CEOLayout } from "@/components/ceo/CEOLayout"
import { 
  ArrowLeft, 
  UserPlus, 
  Search, 
  MoreVertical, 
  Trash2, 
  Phone, 
  Mail,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  AlertTriangle
} from "lucide-react"
import Link from "next/link"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { VendorDetailModal } from "@/components/vendor-detail-modal"

interface Vendor {
  vendor_id: string
  name: string
  email: string
  phone: string
  created_at: number
  updated_at: number
  verified?: boolean
  status?: string
}

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [filteredVendors, setFilteredVendors] = useState<Vendor[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedVendorId, setSelectedVendorId] = useState<string | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [vendorToDelete, setVendorToDelete] = useState<{ id: string; name: string } | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const router = useRouter()

  const [newVendor, setNewVendor] = useState({
    name: "",
    email: "",
    phone: ""
  })

  function handleViewDetails(vendorId: string) {
    setSelectedVendorId(vendorId)
    setIsDetailModalOpen(true)
  }

  function handleCloseDetailModal() {
    setIsDetailModalOpen(false)
    setSelectedVendorId(null)
  }

  function handleDeleteClick(vendorId: string, vendorName: string) {
    setVendorToDelete({ id: vendorId, name: vendorName })
    setIsDeleteDialogOpen(true)
  }

  useEffect(() => {
    fetchVendors()
  }, [])

  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredVendors(vendors)
    } else {
      const query = searchQuery.toLowerCase()
      const filtered = vendors.filter(
        (vendor) =>
          vendor.name.toLowerCase().includes(query) ||
          vendor.email.toLowerCase().includes(query) ||
          vendor.phone.includes(query)
      )
      setFilteredVendors(filtered)
    }
  }, [searchQuery, vendors])

  async function fetchVendors() {
    try {
      const response = await api.get("/ceo/vendors")
      const vendorsList = response.data.data.vendors || []
      setVendors(vendorsList)
      setFilteredVendors(vendorsList)
    } catch (error: any) {
      toast.error("Failed to load vendors")
      if (error.response?.status === 401) {
        router.push("/ceo/login")
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleAddVendor() {
    if (!newVendor.name.trim() || !newVendor.email.trim() || !newVendor.phone.trim()) {
      toast.error("All fields are required")
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(newVendor.email)) {
      toast.error("Please enter a valid email address")
      return
    }

    const phoneRegex = /^(\+234|234|0)[789]\d{9}$/
    if (!phoneRegex.test(newVendor.phone.replace(/\s/g, ""))) {
      toast.error("Please enter a valid Nigerian phone number")
      return
    }

    setIsSubmitting(true)

    try {
      await api.post("/ceo/vendors", {
        name: newVendor.name.trim(),
        email: newVendor.email.trim().toLowerCase(),
        phone: newVendor.phone.replace(/\s/g, "")
      })

      toast.success("Vendor added successfully! OTP sent to vendor.")
      setNewVendor({ name: "", email: "", phone: "" })
      setIsAddDialogOpen(false)
      fetchVendors()
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || "Failed to add vendor"
      toast.error(errorMsg)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDeleteVendor(vendorId: string, vendorName: string) {
    setIsDeleting(true)

    try {
      await api.delete(`/ceo/vendors/${vendorId}`)
      toast.success(`${vendorName} has been removed successfully`)
      setIsDeleteDialogOpen(false)
      setVendorToDelete(null)
      fetchVendors()
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || "Failed to remove vendor"
      toast.error(errorMsg)
    } finally {
      setIsDeleting(false)
    }
  }

  function formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric"
    })
  }

  function formatPhone(phone: string): string {
    if (phone.startsWith("+234")) {
      return phone.replace("+234", "+234 ")
    } else if (phone.startsWith("234")) {
      return phone.replace("234", "+234 ")
    } else if (phone.startsWith("0")) {
      return phone.replace(/^0/, "+234 ")
    }
    return phone
  }

  if (loading) {
    return (
      <CEOLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-muted-foreground">Loading vendors...</p>
          </div>
        </div>
      </CEOLayout>
    )
  }

  return (
    <CEOLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Vendors</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Manage your vendors - {vendors.length} total
            </p>
          </div>

          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <UserPlus className="h-4 w-4" /> Add Vendor
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Vendor</DialogTitle>
                <DialogDescription>
                  Enter vendor details. They will receive an OTP via SMS to create their account.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Bisi Ojo"
                    value={newVendor.name}
                    onChange={(e) => setNewVendor({ ...newVendor, name: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="e.g., bisi@example.com"
                    value={newVendor.email}
                    onChange={(e) => setNewVendor({ ...newVendor, email: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="e.g., +2348012345678 or 08012345678"
                    value={newVendor.phone}
                    onChange={(e) => setNewVendor({ ...newVendor, phone: e.target.value })}
                  />
                  <p className="text-xs text-slate-500">Nigerian phone number (+234, 234, or 0)</p>
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsAddDialogOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button onClick={handleAddVendor} disabled={isSubmitting}>
                  {isSubmitting ? "Adding..." : "Add Vendor"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Search className="h-5 w-5 text-slate-500" />
              <Input
                placeholder="Search by name, email, or phone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>All Vendors</CardTitle>
            <CardDescription>
              {filteredVendors.length} {filteredVendors.length === 1 ? "vendor" : "vendors"} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredVendors.length === 0 ? (
              <div className="text-center py-12">
                <UserPlus className="h-12 w-12 text-slate-400 dark:text-slate-500 mx-auto mb-4" />
                <p className="text-slate-600 dark:text-slate-400 mb-2">
                  {searchQuery ? "No vendors match your search" : "No vendors yet"}
                </p>
                {!searchQuery && (
                  <Button onClick={() => setIsAddDialogOpen(true)} className="mt-4">
                    <UserPlus className="h-4 w-4 mr-2" /> Add Your First Vendor
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Joined</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredVendors.map((vendor) => (
                      <TableRow key={vendor.vendor_id}>
                        <TableCell className="font-medium">{vendor.name}</TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1 text-sm">
                            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                              <Mail className="h-3 w-3" />
                              {vendor.email}
                            </div>
                            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                              <Phone className="h-3 w-3" />
                              {formatPhone(vendor.phone)}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {vendor.verified ? (
                            <Badge variant="default" className="gap-1">
                              <CheckCircle className="h-3 w-3" /> Verified
                            </Badge>
                          ) : vendor.status === "pending" ? (
                            <Badge variant="secondary" className="gap-1">
                              <Clock className="h-3 w-3" /> Pending
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="gap-1">
                              <XCircle className="h-3 w-3" /> Unverified
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-slate-600 dark:text-slate-400">
                          {formatDate(vendor.created_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                className="cursor-pointer"
                                onClick={() => handleViewDetails(vendor.vendor_id)}
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-red-600 cursor-pointer"
                                onClick={() => handleDeleteClick(vendor.vendor_id, vendor.name)}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Remove Vendor
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

      {/* Vendor Detail Modal */}
      <VendorDetailModal
        vendorId={selectedVendorId}
        isOpen={isDetailModalOpen}
        onClose={handleCloseDetailModal}
      />

      {/* Delete Confirmation Modal */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Remove Vendor
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p className="text-base">
                Are you sure you want to remove <span className="font-semibold text-slate-900 dark:text-white">{vendorToDelete?.name}</span>?
              </p>
              <div className="bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800 rounded-md p-3 space-y-2">
                <p className="text-sm font-medium text-orange-800 dark:text-orange-400">⚠️ Warning: This action cannot be undone</p>
                <ul className="text-sm text-orange-700 dark:text-orange-300 space-y-1 ml-4 list-disc">
                  <li>All vendor data will be permanently deleted</li>
                  <li>Vendor will lose access to their dashboard</li>
                  <li>Order history will be retained for audit purposes</li>
                </ul>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => vendorToDelete && handleDeleteVendor(vendorToDelete.id, vendorToDelete.name)}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
            >
              {isDeleting ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Removing...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Yes, Remove Vendor
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
    </CEOLayout>
  )
}
