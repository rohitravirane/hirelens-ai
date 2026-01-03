'use client'

import { useState, useRef, useEffect } from 'react'
import api from '@/lib/api'
import { useQueryClient } from 'react-query'

interface ResumeUploadProps {
  isOpen: boolean
  onClose: () => void
  onUploadSuccess?: (resumeId: number) => void
}

export default function ResumeUpload({ isOpen, onClose, onUploadSuccess }: ResumeUploadProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploadedResumeId, setUploadedResumeId] = useState<number | null>(null)
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'failed'>('idle')
  const [processingMessage, setProcessingMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setFile(null)
      setUploadedResumeId(null)
      setProcessingStatus('idle')
      setProcessingMessage('')
      setError('')
    }
  }, [isOpen])

  // Poll for processing status after upload
  useEffect(() => {
    if (!uploadedResumeId || processingStatus !== 'processing') return

    let checkCount = 0
    const maxChecks = 120 // Maximum 4 minutes (120 * 2 seconds)
    
    const checkStatus = async () => {
      try {
        checkCount++
        const response = await api.get(`/api/v1/resumes/${uploadedResumeId}`)
        const status = response.data.processing_status
        
        if (status === 'completed') {
          setProcessingStatus('completed')
          setProcessingMessage('Resume processed successfully! Extracted data is ready.')
          // Wait 1 second then trigger success callback
          setTimeout(() => {
            if (onUploadSuccess) {
              onUploadSuccess(uploadedResumeId)
            }
            // Close modal after 2 seconds
            setTimeout(() => {
              onClose()
            }, 2000)
          }, 1000)
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
  }, [uploadedResumeId, processingStatus, onUploadSuccess, onClose])

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
      if (droppedFile.type === 'application/pdf' || 
          droppedFile.name.endsWith('.docx') || 
          droppedFile.name.endsWith('.doc')) {
        setFile(droppedFile)
      } else {
        setError('Please upload a PDF or DOCX file')
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError('')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a file')
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
      setUploadedResumeId(response.data.id)
      setProcessingStatus('processing')
      setProcessingMessage('Resume uploaded! Processing started...')
      setLoading(false)
      
      // Don't close modal - keep it open to show processing status
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload resume')
      setProcessingStatus('failed')
      setProcessingMessage('Upload failed. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Upload Resume</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Processing Status */}
          {processingStatus !== 'idle' && (
            <div className={`mb-4 p-4 rounded-lg ${
              processingStatus === 'completed' 
                ? 'bg-green-50 border border-green-200' 
                : processingStatus === 'failed'
                ? 'bg-red-50 border border-red-200'
                : 'bg-blue-50 border border-blue-200'
            }`}>
              <div className="flex items-center space-x-3">
                {processingStatus === 'processing' || processingStatus === 'uploading' ? (
                  <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647A7.962 7.962 0 0112 20c4.418 0 8-3.582 8-8h-4a4 4 0 11-8 0v4z"></path>
                  </svg>
                ) : processingStatus === 'completed' ? (
                  <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
                <div className="flex-1">
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
                      This may take 30-60 seconds. Please keep this window open...
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit}>
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
                  <p className="text-xs text-gray-500">PDF, DOCX, or DOC (Max 10MB)</p>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="mt-2 inline-block px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 cursor-pointer"
              >
                Select File
              </label>
            </div>

            <div className="mt-4 flex flex-col-reverse sm:flex-row justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                disabled={processingStatus === 'processing' || processingStatus === 'uploading'}
                className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {processingStatus === 'completed' ? 'Close' : 'Cancel'}
              </button>
              {processingStatus === 'idle' && (
                <button
                  type="submit"
                  disabled={loading || !file}
                  className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                >
                  {loading ? 'Uploading...' : 'Upload Resume'}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

