'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { useQueryClient } from 'react-query'

interface CandidateModalProps {
  isOpen: boolean
  onClose: () => void
  resumeId?: number
}

export default function CandidateModal({ isOpen, onClose, resumeId }: CandidateModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [resumes, setResumes] = useState<any[]>([])
  const [loadingResumeData, setLoadingResumeData] = useState(false)
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    linkedin_url: '',
    portfolio_url: '',
    resume_id: resumeId || '',
    notes: '',
  })
  const queryClient = useQueryClient()

  useEffect(() => {
    if (isOpen) {
      fetchResumes()
      if (resumeId) {
        setFormData(prev => ({ ...prev, resume_id: resumeId }))
        // Retry fetching personal info with exponential backoff
        // This handles cases where processing just completed
        fetchResumePersonalInfoWithRetry(resumeId)
      }
    }
  }, [isOpen, resumeId])

  const fetchResumes = async () => {
    try {
      const response = await api.get('/api/v1/resumes/')
      setResumes(response.data)
    } catch (err) {
      console.error('Failed to fetch resumes', err)
    }
  }

  const fetchResumePersonalInfoWithRetry = async (id: number, retryCount = 0) => {
    const maxRetries = 10 // Increased retries for better reliability
    const retryDelay = 1000 * Math.pow(1.5, retryCount) // Slower backoff: 1s, 1.5s, 2.25s, 3.4s, etc.
    
    if (retryCount === 0) {
      setLoadingResumeData(true)
    }
    
    try {
      const response = await api.get(`/api/v1/resumes/${id}`)
      const latestVersion = response.data.latest_version
      
      // Check if resume is still processing
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
      } else if (retryCount < maxRetries) {
        // Data not ready yet, retry after delay
        setTimeout(() => {
          fetchResumePersonalInfoWithRetry(id, retryCount + 1)
        }, retryDelay)
      } else {
        setLoadingResumeData(false)
      }
    } catch (err) {
      console.error('Failed to fetch resume personal info', err)
      // Retry on error if we haven't exceeded max retries
      if (retryCount < maxRetries) {
        setTimeout(() => {
          fetchResumePersonalInfoWithRetry(id, retryCount + 1)
        }, retryDelay)
      } else {
        setLoadingResumeData(false)
      }
    }
  }

  const fetchResumePersonalInfo = async (id: number) => {
    fetchResumePersonalInfoWithRetry(id)
  }

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.post('/api/v1/candidates/', {
        ...formData,
        resume_id: parseInt(formData.resume_id as string),
      })
      queryClient.invalidateQueries('candidates')
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        linkedin_url: '',
        portfolio_url: '',
        resume_id: resumeId || '',
        notes: '',
      })
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
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Add Candidate</h2>
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

          {loadingResumeData && resumeId && (
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Resume *
              </label>
              <select
                required
                value={formData.resume_id}
                onChange={(e) => setFormData({ ...formData, resume_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900"
              >
                <option value="">Select a resume</option>
                {resumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.file_name} {resume.processing_status === 'completed' ? '✓' : '(Processing...)'}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Upload a resume first if you don't see any options
              </p>
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
        </div>
      </div>
    </div>
  )
}

