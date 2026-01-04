'use client'

import { useState, useEffect, useRef } from 'react'
import api from '@/lib/api'
import { useQueryClient } from 'react-query'

interface AddCandidateModalProps {
  isOpen: boolean
  onClose: () => void
}

type Step = 'upload' | 'form' | 'processing'

export default function AddCandidateModal({ isOpen, onClose }: AddCandidateModalProps) {
  const [step, setStep] = useState<Step>('upload')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [resumeId, setResumeId] = useState<number | null>(null)
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'failed'>('idle')
  const [processingMessage, setProcessingMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    linkedin_url: '',
    portfolio_url: '',
    notes: '',
  })
  const [loadingResumeData, setLoadingResumeData] = useState(false)

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setFile(null)
      setResumeId(null)
      setStep('upload')
      setProcessingStatus('idle')
      setProcessingMessage('')
      setError('')
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        linkedin_url: '',
        portfolio_url: '',
        notes: '',
      })
    }
  }, [isOpen])

  // Poll for processing status after upload
  useEffect(() => {
    if (!resumeId || processingStatus !== 'processing') return

    let checkCount = 0
    const maxChecks = 120 // Maximum 4 minutes (120 * 2 seconds)
    
    const checkStatus = async () => {
      try {
        checkCount++
        const response = await api.get(`/api/v1/resumes/${resumeId}`)
        const status = response.data.processing_status
        
        if (status === 'completed') {
          setProcessingStatus('completed')
          setProcessingMessage('Resume processed successfully!')
          // Fetch resume data and populate form
          fetchResumePersonalInfoWithRetry(resumeId)
        } else if (status === 'failed') {
          setProcessingStatus('failed')
          setProcessingMessage('Resume processing failed. Please try again or upload a different file.')
        } else if (status === 'processing') {
          setProcessingMessage(`Processing resume... (${checkCount * 2}s)`)
          if (checkCount < maxChecks) {
            setTimeout(checkStatus, 2000)
          } else {
            setProcessingStatus('failed')
            setProcessingMessage('Processing is taking longer than expected. Please check back later.')
          }
        } else if (status === 'pending') {
          setProcessingMessage('Resume queued for processing...')
          setTimeout(checkStatus, 2000)
        }
      } catch (err) {
        console.error('Failed to check processing status', err)
        if (checkCount >= maxChecks) {
          setProcessingStatus('failed')
          setProcessingMessage('Unable to check processing status. Please try again later.')
        } else {
          setTimeout(checkStatus, 2000)
        }
      }
    }
    
    // Start checking after 2 seconds
    setTimeout(checkStatus, 2000)
  }, [resumeId, processingStatus])

  const fetchResumePersonalInfoWithRetry = async (id: number, retryCount = 0) => {
    const maxRetries = 10
    const retryDelay = 1000 * Math.pow(1.5, retryCount)
    
    if (retryCount === 0) {
      setLoadingResumeData(true)
    }
    
    try {
      const response = await api.get(`/api/v1/resumes/${id}`)
      const latestVersion = response.data.latest_version
      
      if (response.data.processing_status === 'processing' || response.data.processing_status === 'pending') {
        if (retryCount < maxRetries) {
          setTimeout(() => {
            fetchResumePersonalInfoWithRetry(id, retryCount + 1)
          }, retryDelay)
        } else {
          setLoadingResumeData(false)
        }
        return
      }
      
      // Data is available, populate form
      if (latestVersion && (latestVersion.first_name || latestVersion.email || latestVersion.phone)) {
        setFormData(prev => ({
          ...prev,
          first_name: latestVersion.first_name || prev.first_name,
          last_name: latestVersion.last_name || prev.last_name,
          email: latestVersion.email || prev.email,
          phone: latestVersion.phone || prev.phone,
          linkedin_url: latestVersion.linkedin_url || prev.linkedin_url,
          portfolio_url: latestVersion.portfolio_url || prev.portfolio_url,
        }))
        setLoadingResumeData(false)
        // Move to form step
        setTimeout(() => {
          setStep('form')
        }, 500)
      } else if (retryCount < maxRetries) {
        setTimeout(() => {
          fetchResumePersonalInfoWithRetry(id, retryCount + 1)
        }, retryDelay)
      } else {
        setLoadingResumeData(false)
        // Still move to form step even if data not ready
        setTimeout(() => {
          setStep('form')
        }, 500)
      }
    } catch (err) {
      console.error('Failed to fetch resume personal info', err)
      if (retryCount < maxRetries) {
        setTimeout(() => {
          fetchResumePersonalInfoWithRetry(id, retryCount + 1)
        }, retryDelay)
      } else {
        setLoadingResumeData(false)
        // Move to form step anyway
        setTimeout(() => {
          setStep('form')
        }, 500)
      }
    }
  }

  if (!isOpen) return null

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type === 'application/pdf' || droppedFile.name.endsWith('.pdf')) {
        setFile(droppedFile)
        setError('')
      } else {
        setError('Only PDF resume files are allowed. Please upload a PDF file.')
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (selectedFile.type === 'application/pdf' || selectedFile.name.endsWith('.pdf')) {
        setFile(selectedFile)
        setError('')
      } else {
        setError('Only PDF resume files are allowed. Please upload a PDF file.')
      }
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a PDF resume file')
      return
    }

    setError('')
    setLoading(true)
    setProcessingStatus('uploading')
    setProcessingMessage('Uploading resume...')

    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/api/v1/resumes/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      queryClient.invalidateQueries('resumes')
      setResumeId(response.data.id)
      setProcessingStatus('processing')
      setProcessingMessage('Resume uploaded! Processing started...')
      setStep('processing')
      setLoading(false)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to upload resume'
      setError(errorMessage)
      setProcessingStatus('failed')
      setProcessingMessage('Upload failed. Please try again.')
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!resumeId) {
      setError('Resume is required')
      return
    }

    setError('')
    setLoading(true)

    try {
      await api.post('/api/v1/candidates/', {
        ...formData,
        resume_id: resumeId,
      })
      queryClient.invalidateQueries('candidates')
      queryClient.invalidateQueries('resumes')
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create candidate')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex justify-between items-center mb-4 gap-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Add Candidate</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Step Indicator */}
          <div className="mb-6">
            <div className="flex items-center justify-center space-x-4">
              <div className={`flex items-center ${step === 'upload' || step === 'processing' || step === 'form' ? 'text-primary-600' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'upload' || step === 'processing' || step === 'form' ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                  1
                </div>
                <span className="ml-2 text-sm font-medium">Upload Resume</span>
              </div>
              <div className={`w-12 h-0.5 ${step === 'processing' || step === 'form' ? 'bg-primary-600' : 'bg-gray-300'}`}></div>
              <div className={`flex items-center ${step === 'form' ? 'text-primary-600' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'form' ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                  2
                </div>
                <span className="ml-2 text-sm font-medium">Add Details</span>
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Upload Step */}
          {step === 'upload' && (
            <form onSubmit={handleUpload}>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {file ? (
                  <div className="space-y-2">
                    <svg className="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setFile(null)
                        if (fileInputRef.current) {
                          fileInputRef.current.value = ''
                        }
                      }}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-sm text-gray-600">
                      <span className="font-medium text-primary-600">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-gray-500">PDF Resume only (Max 10MB)</p>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="mt-2 inline-block px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 cursor-pointer"
                >
                  Select PDF File
                </label>
              </div>

              <div className="mt-4 flex flex-col-reverse sm:flex-row justify-end gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !file}
                  className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                >
                  {loading ? 'Uploading...' : 'Upload Resume'}
                </button>
              </div>
            </form>
          )}

          {/* Processing Step */}
          {step === 'processing' && (
            <div className="text-center py-8">
              <div className={`p-4 rounded-lg ${
                processingStatus === 'completed' 
                  ? 'bg-green-50 border border-green-200' 
                  : processingStatus === 'failed'
                  ? 'bg-red-50 border border-red-200'
                  : 'bg-blue-50 border border-blue-200'
              }`}>
                <div className="flex items-center justify-center space-x-3">
                  {processingStatus === 'processing' || processingStatus === 'uploading' ? (
                    <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647A7.962 7.962 0 0112 20c4.418 0 8-3.582 8-8h-4a4 4 0 11-8 0v4z"></path>
                    </svg>
                  ) : processingStatus === 'completed' ? (
                    <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                  <div>
                    <p className={`text-sm font-medium ${
                      processingStatus === 'completed' 
                        ? 'text-green-800' 
                        : processingStatus === 'failed'
                        ? 'text-red-800'
                        : 'text-blue-800'
                    }`}>
                      {processingMessage || 'Processing...'}
                    </p>
                    {processingStatus === 'processing' && (
                      <p className="text-xs text-blue-600 mt-1">
                        Extracting data from resume...
                      </p>
                    )}
                  </div>
                </div>
              </div>
              {processingStatus === 'failed' && (
                <div className="mt-4 flex justify-center gap-3">
                  <button
                    onClick={() => {
                      setStep('upload')
                      setProcessingStatus('idle')
                      setFile(null)
                      setResumeId(null)
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Try Again
                  </button>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Form Step */}
          {step === 'form' && (
            <>
              {loadingResumeData && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-blue-700 text-sm flex items-center space-x-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647A7.962 7.962 0 0112 20c4.418 0 8-3.582 8-8h-4a4 4 0 11-8 0v4z"></path>
                  </svg>
                  <span>Loading extracted data from resume...</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      First Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email *
                    </label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      LinkedIn URL
                    </label>
                    <input
                      type="url"
                      value={formData.linkedin_url}
                      onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
                      placeholder="https://linkedin.com/in/..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Portfolio URL
                    </label>
                    <input
                      type="url"
                      value={formData.portfolio_url}
                      onChange={(e) => setFormData({ ...formData, portfolio_url: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
                      placeholder="https://..."
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    rows={3}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
                    placeholder="Additional notes about the candidate..."
                  />
                </div>

                <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={onClose}
                    className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Add Candidate'}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

