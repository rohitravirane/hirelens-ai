'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'

interface JobDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  jobId: number | null
  onViewRankings?: () => void
}

export default function JobDetailsModal({ isOpen, onClose, jobId, onViewRankings }: JobDetailsModalProps) {
  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen && jobId) {
      fetchJobDetails()
    }
  }, [isOpen, jobId])

  const fetchJobDetails = async () => {
    if (!jobId) return
    
    setLoading(true)
    setError('')
    try {
      const response = await api.get(`/api/v1/jobs/${jobId}`)
      setJob(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load job details')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen || !jobId) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700 m-6">
            {error}
          </div>
        ) : job ? (
          <>
            {/* Sticky Header */}
            <div className="sticky top-0 bg-white z-10 border-b border-gray-200 px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4">
              <div className="flex justify-between items-start gap-3">
                <div className="flex-1 min-w-0 pr-2 sm:pr-4">
                  <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-2 break-words">{job.title}</h2>
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs sm:text-sm text-gray-600">
                    {job.company && (
                      <span className="font-medium">{job.company}</span>
                    )}
                    {job.department && (
                      <span className="text-gray-400">•</span>
                    )}
                    {job.department && (
                      <span>{job.department}</span>
                    )}
                    {job.location && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span>{job.location}</span>
                      </>
                    )}
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 flex-shrink-0"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-4 sm:px-6">

              {/* Job Info Badges */}
              <div className="flex flex-wrap gap-2 mb-6 pt-4">
                {job.experience_years_required && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                    {job.experience_years_required}+ years experience
                  </span>
                )}
                {job.seniority_level && (
                  <span className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full capitalize">
                    {job.seniority_level}
                  </span>
                )}
                {job.employment_type && (
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full capitalize">
                    {job.employment_type.replace('-', ' ')}
                  </span>
                )}
                {job.remote_allowed && (
                  <span className="px-3 py-1 bg-orange-100 text-orange-800 text-sm rounded-full">
                    Remote Allowed
                  </span>
                )}
              </div>

              {/* Required Skills */}
              {job.required_skills && job.required_skills.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3">Required Skills</h3>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    {job.required_skills.map((skill: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 sm:px-3 py-0.5 sm:py-1 bg-blue-100 text-blue-800 text-xs sm:text-sm rounded-full break-words"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Nice to Have Skills */}
              {job.nice_to_have_skills && job.nice_to_have_skills.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3">Nice to Have Skills</h3>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    {job.nice_to_have_skills.map((skill: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 sm:px-3 py-0.5 sm:py-1 bg-gray-100 text-gray-700 text-xs sm:text-sm rounded-full break-words"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Education Requirements */}
              {job.education_requirements && job.education_requirements.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Education Requirements</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {job.education_requirements.map((req: string, i: number) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Full Job Description */}
              {job.raw_text && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Job Description</h3>
                  <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                      {job.raw_text}
                    </pre>
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="pt-4 border-t text-xs text-gray-500">
                <p>Created: {new Date(job.created_at).toLocaleString()}</p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 mt-6 pt-6 border-t pb-6">
                <button
                  onClick={onClose}
                  className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
                {onViewRankings && (
                  <button
                    onClick={() => {
                      onViewRankings()
                      onClose()
                    }}
                    className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                  >
                    View Rankings
                  </button>
                )}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

