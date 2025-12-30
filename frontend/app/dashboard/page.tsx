'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import JobModal from '@/components/JobModal'
import ResumeUpload from '@/components/ResumeUpload'
import CandidateModal from '@/components/CandidateModal'
import JobDetailsModal from '@/components/JobDetailsModal'
import CandidateDetailsModal from '@/components/CandidateDetailsModal'
import BulkReprocessModal from '@/components/BulkReprocessModal'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const queryClient = useQueryClient()
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [showJobModal, setShowJobModal] = useState(false)
  const [showResumeModal, setShowResumeModal] = useState(false)
  const [showCandidateModal, setShowCandidateModal] = useState(false)
  const [showJobDetailsModal, setShowJobDetailsModal] = useState(false)
  const [showCandidateDetailsModal, setShowCandidateDetailsModal] = useState(false)
  const [showBulkReprocessModal, setShowBulkReprocessModal] = useState(false)
  const [selectedJobDetailsId, setSelectedJobDetailsId] = useState<number | null>(null)
  const [selectedCandidateDetailsId, setSelectedCandidateDetailsId] = useState<number | null>(null)
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<'jobs' | 'candidates' | 'rankings'>('jobs')
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [matchingCandidateId, setMatchingCandidateId] = useState<number | null>(null)

  const { data: jobs, isLoading: jobsLoading } = useQuery(
    'jobs',
    async () => {
      const response = await api.get('/api/v1/jobs/', { params: { is_active: true } })
      return response.data
    }
  )

  const { data: candidates, isLoading: candidatesLoading } = useQuery(
    'candidates',
    async () => {
      const response = await api.get('/api/v1/candidates/')
      return response.data
    }
  )
  
  // Auto-refetch if there are low-quality resumes being processed
  useEffect(() => {
    if (!candidates) return
    
    const hasLowQuality = candidates.some((c: any) => 
      c.resume_id && (c.resume_quality_score === null || c.resume_quality_score < 80)
    )
    
    if (hasLowQuality) {
      const interval = setInterval(() => {
        queryClient.invalidateQueries('candidates')
      }, 5000) // Refetch every 5 seconds
      
      return () => clearInterval(interval)
    }
  }, [candidates, queryClient])

  const { data: resumes, isLoading: resumesLoading } = useQuery(
    'resumes',
    async () => {
      const response = await api.get('/api/v1/resumes/')
      return response.data
    },
    {
      refetchInterval: 5000, // Refetch every 5 seconds to show processing status
    }
  )

  const { data: rankings, isLoading: rankingsLoading } = useQuery(
    ['rankings', selectedJobId],
    async () => {
      if (!selectedJobId) return null
      const response = await api.get(`/api/v1/matching/job/${selectedJobId}/rankings`)
      return response.data
    },
    { enabled: !!selectedJobId }
  )

  const matchMutation = useMutation(
    async ({ candidateId, jobId }: { candidateId: number; jobId: number }) => {
      setMatchingCandidateId(candidateId)
      return api.post(`/api/v1/matching/match?candidate_id=${candidateId}&job_id=${jobId}`)
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['rankings', selectedJobId])
        queryClient.invalidateQueries('candidates')
        setMatchingCandidateId(null)
        setNotification({ 
          type: 'success', 
          message: `Candidate matched successfully! Score: ${data.data?.overall_score?.toFixed(1) || 'N/A'}%` 
        })
        // Auto switch to rankings tab
        setActiveTab('rankings')
        // Clear notification after 3 seconds
        setTimeout(() => setNotification(null), 3000)
      },
      onError: (error: any) => {
        setMatchingCandidateId(null)
        setNotification({ 
          type: 'error', 
          message: error.response?.data?.detail || 'Failed to match candidate. Please try again.' 
        })
        setTimeout(() => setNotification(null), 5000)
      },
    }
  )

  const bulkMatchMutation = useMutation(
    async (jobId: number) => {
      if (!candidates || candidates.length === 0) return
      const promises = candidates.map((candidate: any) =>
        api.post(`/api/v1/matching/match?candidate_id=${candidate.id}&job_id=${jobId}`)
      )
      await Promise.all(promises)
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['rankings', selectedJobId])
        setNotification({ 
          type: 'success', 
          message: `Successfully matched ${candidates?.length || 0} candidates!` 
        })
        setActiveTab('rankings')
        setTimeout(() => setNotification(null), 3000)
      },
      onError: (error: any) => {
        setNotification({ 
          type: 'error', 
          message: error.response?.data?.detail || 'Failed to match candidates. Please try again.' 
        })
        setTimeout(() => setNotification(null), 5000)
      },
    }
  )

  const handleMatchAll = () => {
    if (selectedJobId && candidates && candidates.length > 0) {
      bulkMatchMutation.mutate(selectedJobId)
    }
  }

  const handleResumeUploadSuccess = (resumeId: number) => {
    setSelectedResumeId(resumeId)
    setShowResumeModal(false)
    setShowCandidateModal(true)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notification Toast */}
      {notification && (
        <div className="fixed top-4 right-4 left-4 sm:left-auto z-50 animate-slide-in">
          <div className={`rounded-lg shadow-lg p-4 max-w-md mx-auto sm:mx-0 ${
            notification.type === 'success' 
              ? 'bg-green-50 border border-green-200' 
              : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center">
              {notification.type === 'success' ? (
                <svg className="w-5 h-5 text-green-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-red-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              <p className={`text-sm font-medium ${
                notification.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                {notification.message}
              </p>
              <button
                onClick={() => setNotification(null)}
                className="ml-4 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">HireLens AI</h1>
          <div className="flex items-center space-x-3 sm:space-x-4 w-full sm:w-auto justify-between sm:justify-end">
            <span className="text-xs sm:text-sm text-gray-600 truncate max-w-[150px] sm:max-w-none">{user?.email}</span>
            <button
              onClick={logout}
              className="text-xs sm:text-sm text-primary-600 hover:text-primary-700 px-3 py-1 rounded hover:bg-gray-100 whitespace-nowrap"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200 overflow-x-auto overflow-y-hidden -mx-4 sm:mx-0 px-4 sm:px-0">
            <nav className="-mb-px flex space-x-4 sm:space-x-8 min-w-max sm:min-w-0">
              <button
                onClick={() => setActiveTab('jobs')}
                className={`py-4 px-2 sm:px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === 'jobs'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Jobs
              </button>
              <button
                onClick={() => setActiveTab('candidates')}
                className={`py-4 px-2 sm:px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === 'candidates'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Candidates
              </button>
              <button
                onClick={() => setActiveTab('rankings')}
                className={`py-4 px-2 sm:px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === 'rankings'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Rankings
              </button>
            </nav>
          </div>
        </div>

        {/* Jobs Tab */}
        {activeTab === 'jobs' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900">Job Descriptions</h2>
              <button
                onClick={() => setShowJobModal(true)}
                className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 flex items-center justify-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Create Job</span>
              </button>
            </div>

            {jobsLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-500">Loading jobs...</p>
              </div>
            ) : jobs && jobs.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {jobs.map((job: any) => (
                  <div
                    key={job.id}
                    className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{job.title}</h3>
                    <p className="text-sm text-gray-600 mb-4">{job.company}</p>
                    {job.required_skills && job.required_skills.length > 0 && (
                      <div className="mt-4">
                        <p className="text-xs text-gray-500 mb-2">Required Skills:</p>
                        <div className="flex flex-wrap gap-1">
                          {job.required_skills.slice(0, 5).map((skill: string, i: number) => (
                            <span
                              key={i}
                              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                            >
                              {skill}
                            </span>
                          ))}
                          {job.required_skills.length > 5 && (
                            <span className="px-2 py-1 text-gray-500 text-xs">
                              +{job.required_skills.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                    <div className="mt-4 pt-4 border-t flex flex-col sm:flex-row gap-2">
                      <span className="text-xs text-gray-500">
                        Created: {new Date(job.created_at).toLocaleDateString()}
                      </span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedJobDetailsId(job.id)
                            setShowJobDetailsModal(true)
                          }}
                          className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                        >
                          View Details
                        </button>
                        <span className="text-gray-300">|</span>
                        <button
                          onClick={() => {
                            setSelectedJobId(job.id)
                            setActiveTab('rankings')
                          }}
                          className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                        >
                          View Rankings
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">No jobs yet</h3>
                <p className="mt-2 text-sm text-gray-500">Get started by creating your first job description</p>
                <button
                  onClick={() => setShowJobModal(true)}
                  className="mt-6 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                >
                  Create Job
                </button>
              </div>
            )}
          </div>
        )}

        {/* Candidates Tab */}
        {activeTab === 'candidates' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900">Candidates</h2>
              <div className="flex flex-col sm:flex-row w-full sm:w-auto gap-2 sm:gap-3">
                {candidates && candidates.some((c: any) => c.resume_id && (c.resume_quality_score === null || c.resume_quality_score < 80)) && (
                  <button
                    onClick={() => setShowBulkReprocessModal(true)}
                    className="w-full sm:w-auto px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 flex items-center justify-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span>Reprocess Low Quality</span>
                  </button>
                )}
                <button
                  onClick={() => setShowResumeModal(true)}
                  className="w-full sm:w-auto px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center justify-center space-x-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span>Upload Resume</span>
                </button>
                <button
                  onClick={() => setShowCandidateModal(true)}
                  className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 flex items-center justify-center space-x-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span>Add Candidate</span>
                </button>
              </div>
            </div>

            {candidatesLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-500">Loading candidates...</p>
              </div>
            ) : candidates && candidates.length > 0 ? (
              <>
                {/* Desktop Table View */}
                <div className="hidden md:block bg-white rounded-lg shadow overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quality
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {candidates.map((candidate: any) => (
                        <tr key={candidate.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {candidate.first_name} {candidate.last_name}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500">{candidate.email}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined ? (
                              <div className="flex items-center gap-2">
                                <div className="flex-1 bg-gray-200 rounded-full h-2 w-16">
                                  <div 
                                    className={`h-2 rounded-full ${
                                      candidate.resume_quality_score >= 80 ? 'bg-green-500' :
                                      candidate.resume_quality_score >= 50 ? 'bg-yellow-500' :
                                      'bg-red-500'
                                    }`}
                                    style={{ width: `${candidate.resume_quality_score}%` }}
                                  ></div>
                                </div>
                                <span className={`text-xs font-semibold ${
                                  candidate.resume_quality_score >= 80 ? 'text-green-700' :
                                  candidate.resume_quality_score >= 50 ? 'text-yellow-700' :
                                  'text-red-700'
                                }`}>
                                  {candidate.resume_quality_score}%
                                </span>
                              </div>
                            ) : (
                              <span className="text-xs text-gray-400">N/A</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              candidate.status === 'active' ? 'bg-green-100 text-green-800' :
                              candidate.status === 'shortlisted' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {candidate.status || 'active'}
                            </span>
                          </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => {
                                setSelectedCandidateDetailsId(candidate.id)
                                setShowCandidateDetailsModal(true)
                              }}
                              className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-md transition-colors"
                              title="View Details"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            </button>
                            {selectedJobId && (
                              <button
                                onClick={() => {
                                  // Block matching if quality is too low
                                  if (candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80) {
                                    setNotification({
                                      type: 'error',
                                      message: `Cannot match: Resume quality is ${candidate.resume_quality_score}%. Please reprocess resume to improve quality (minimum 80% required).`
                                    })
                                    setTimeout(() => setNotification(null), 5000)
                                    return
                                  }
                                  matchMutation.mutate({ candidateId: candidate.id, jobId: selectedJobId })
                                }}
                                disabled={matchMutation.isLoading || matchingCandidateId === candidate.id || (candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80)}
                                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                                  matchMutation.isLoading && matchingCandidateId === candidate.id
                                    ? 'bg-primary-100 text-primary-700 cursor-wait'
                                    : (candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80)
                                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                    : 'bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed'
                                }`}
                                title={candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80 ? 'Resume quality too low. Reprocess required.' : ''}
                              >
                                {matchMutation.isLoading && matchingCandidateId === candidate.id ? (
                                  <span className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647A7.962 7.962 0 0112 20c4.418 0 8-3.582 8-8h-4a4 4 0 11-8 0v4z"></path>
                                    </svg>
                                    Matching...
                                  </span>
                                ) : (
                                  'Match'
                                )}
                              </button>
                            )}
                          </div>
                        </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {/* Mobile Card View */}
                <div className="md:hidden space-y-3">
                  {candidates.map((candidate: any) => (
                    <div key={candidate.id} className="bg-white rounded-lg shadow p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-gray-900">
                            {candidate.first_name} {candidate.last_name}
                          </h3>
                          <p className="text-xs text-gray-500 mt-1">{candidate.email}</p>
                          {candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && (
                            <div className="flex items-center gap-2 mt-2">
                              <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                                <div 
                                  className={`h-1.5 rounded-full ${
                                    candidate.resume_quality_score >= 80 ? 'bg-green-500' :
                                    candidate.resume_quality_score >= 50 ? 'bg-yellow-500' :
                                    'bg-red-500'
                                  }`}
                                  style={{ width: `${candidate.resume_quality_score}%` }}
                                ></div>
                              </div>
                              <span className={`text-xs font-semibold ${
                                candidate.resume_quality_score >= 80 ? 'text-green-700' :
                                candidate.resume_quality_score >= 50 ? 'text-yellow-700' :
                                'text-red-700'
                              }`}>
                                {candidate.resume_quality_score}%
                              </span>
                            </div>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          candidate.status === 'active' ? 'bg-green-100 text-green-800' :
                          candidate.status === 'shortlisted' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {candidate.status || 'active'}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedCandidateDetailsId(candidate.id)
                            setShowCandidateDetailsModal(true)
                          }}
                          className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors flex items-center justify-center gap-2"
                          title="View Details"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          Details
                        </button>
                        {selectedJobId && (
                          <button
                            onClick={() => {
                              // Block matching if quality is too low
                              if (candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80) {
                                setNotification({
                                  type: 'error',
                                  message: `Cannot match: Resume quality is ${candidate.resume_quality_score}%. Please reprocess resume to improve quality (minimum 80% required).`
                                })
                                setTimeout(() => setNotification(null), 5000)
                                return
                              }
                              matchMutation.mutate({ candidateId: candidate.id, jobId: selectedJobId })
                            }}
                            disabled={matchMutation.isLoading || matchingCandidateId === candidate.id || (candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80)}
                            className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                              matchMutation.isLoading && matchingCandidateId === candidate.id
                                ? 'bg-primary-100 text-primary-700 cursor-wait'
                                : (candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80)
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed'
                            }`}
                            title={candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && candidate.resume_quality_score < 80 ? 'Resume quality too low. Reprocess required.' : ''}
                          >
                            {matchMutation.isLoading && matchingCandidateId === candidate.id ? (
                              <span className="flex items-center justify-center">
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647A7.962 7.962 0 0112 20c4.418 0 8-3.582 8-8h-4a4 4 0 11-8 0v4z"></path>
                                </svg>
                                Matching...
                              </span>
                            ) : (
                              'Match'
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">No candidates yet</h3>
                <p className="mt-2 text-sm text-gray-500">Upload a resume and add candidates to get started</p>
                <div className="mt-6 flex justify-center space-x-3">
                  <button
                    onClick={() => setShowResumeModal(true)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                  >
                    Upload Resume
                  </button>
                  <button
                    onClick={() => setShowCandidateModal(true)}
                    className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                  >
                    Add Candidate
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Rankings Tab */}
        {activeTab === 'rankings' && (
          <div className="space-y-6">
            <div className="flex flex-col gap-4">
              <div>
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900">Candidate Rankings</h2>
                {selectedJobId && jobs && (
                  <p className="text-xs sm:text-sm text-gray-500 mt-1">
                    {jobs.find((j: any) => j.id === selectedJobId)?.title} - {jobs.find((j: any) => j.id === selectedJobId)?.company}
                  </p>
                )}
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <select
                  value={selectedJobId || ''}
                  onChange={(e) => setSelectedJobId(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                >
                  <option value="">Select a job</option>
                  {jobs?.map((job: any) => (
                    <option key={job.id} value={job.id}>
                      {job.title} - {job.company}
                    </option>
                  ))}
                </select>
                {selectedJobId && candidates && candidates.length > 0 && (
                  <button
                    onClick={handleMatchAll}
                    disabled={bulkMatchMutation.isLoading}
                    className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>{bulkMatchMutation.isLoading ? 'Matching...' : 'Match All Candidates'}</span>
                  </button>
                )}
              </div>
            </div>

            {!selectedJobId ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">Select a job to view rankings</h3>
                <p className="mt-2 text-sm text-gray-500">Choose a job from the dropdown above to see candidate rankings</p>
              </div>
            ) : rankingsLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-500">Loading rankings...</p>
              </div>
            ) : rankings && rankings.length > 0 ? (
              <div className="bg-white rounded-lg shadow divide-y">
                {rankings.map((ranking: any, index: number) => (
                  <div key={ranking.candidate_id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${
                            index === 0 ? 'bg-yellow-100 text-yellow-800' :
                            index === 1 ? 'bg-gray-100 text-gray-800' :
                            index === 2 ? 'bg-orange-100 text-orange-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            #{index + 1}
                          </div>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {ranking.candidate_name || 'Unknown Candidate'}
                          </h3>
                          <p className="text-sm text-gray-500">{ranking.candidate_email}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-primary-600">
                          {ranking.match_result.overall_score.toFixed(1)}
                        </div>
                        <div className="text-sm text-gray-500">Match Score</div>
                        <div className="mt-2">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${
                              ranking.match_result.confidence_level === 'high'
                                ? 'bg-green-100 text-green-800'
                                : ranking.match_result.confidence_level === 'medium'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {ranking.match_result.confidence_level?.toUpperCase() || 'MEDIUM'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* AI Explanation */}
                    {ranking.match_result.ai_explanation && (
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <h4 className="font-semibold text-sm text-gray-700 mb-2">AI Analysis</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          {ranking.match_result.ai_explanation.summary}
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          {ranking.match_result.ai_explanation.strengths && ranking.match_result.ai_explanation.strengths.length > 0 && (
                            <div>
                              <span className="text-xs font-semibold text-green-700">Strengths:</span>
                              <ul className="list-disc list-inside text-xs text-gray-600 mt-1 space-y-1">
                                {ranking.match_result.ai_explanation.strengths.slice(0, 3).map((strength: string, i: number) => (
                                  <li key={i}>{strength}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {ranking.match_result.ai_explanation.weaknesses && ranking.match_result.ai_explanation.weaknesses.length > 0 && (
                            <div>
                              <span className="text-xs font-semibold text-red-700">Gaps:</span>
                              <ul className="list-disc list-inside text-xs text-gray-600 mt-1 space-y-1">
                                {ranking.match_result.ai_explanation.weaknesses.slice(0, 3).map((weakness: string, i: number) => (
                                  <li key={i}>{weakness}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Score Breakdown */}
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
                      <div className="text-center p-2 sm:p-3 bg-blue-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Skills</div>
                        <div className="text-base sm:text-lg font-semibold text-blue-700">
                          {ranking.match_result.skill_match_score?.toFixed(0) || '0'}
                        </div>
                      </div>
                      <div className="text-center p-2 sm:p-3 bg-green-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Experience</div>
                        <div className="text-base sm:text-lg font-semibold text-green-700">
                          {ranking.match_result.experience_score?.toFixed(0) || '0'}
                        </div>
                      </div>
                      <div className="text-center p-2 sm:p-3 bg-purple-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Projects</div>
                        <div className="text-base sm:text-lg font-semibold text-purple-700">
                          {ranking.match_result.project_similarity_score?.toFixed(0) || '0'}
                        </div>
                      </div>
                      <div className="text-center p-2 sm:p-3 bg-orange-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Domain</div>
                        <div className="text-base sm:text-lg font-semibold text-orange-700">
                          {ranking.match_result.domain_familiarity_score?.toFixed(0) || '0'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">No rankings yet</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Match candidates to this job to see rankings
                </p>
                {candidates && candidates.length > 0 && (
                  <button
                    onClick={handleMatchAll}
                    disabled={bulkMatchMutation.isLoading}
                    className="mt-6 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {bulkMatchMutation.isLoading ? 'Matching...' : 'Match All Candidates'}
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Modals */}
      <JobModal isOpen={showJobModal} onClose={() => setShowJobModal(false)} />
      <ResumeUpload
        isOpen={showResumeModal}
        onClose={() => setShowResumeModal(false)}
        onUploadSuccess={handleResumeUploadSuccess}
      />
      <CandidateModal
        isOpen={showCandidateModal}
        onClose={() => {
          setShowCandidateModal(false)
          setSelectedResumeId(null)
        }}
        resumeId={selectedResumeId || undefined}
      />
      <JobDetailsModal
        isOpen={showJobDetailsModal}
        onClose={() => {
          setShowJobDetailsModal(false)
          setSelectedJobDetailsId(null)
        }}
        jobId={selectedJobDetailsId}
        onViewRankings={() => {
          if (selectedJobDetailsId) {
            setSelectedJobId(selectedJobDetailsId)
            setActiveTab('rankings')
          }
        }}
      />
      <CandidateDetailsModal
        isOpen={showCandidateDetailsModal}
        onClose={() => {
          setShowCandidateDetailsModal(false)
          setSelectedCandidateDetailsId(null)
        }}
        candidateId={selectedCandidateDetailsId}
      />
      <BulkReprocessModal
        isOpen={showBulkReprocessModal}
        onClose={() => setShowBulkReprocessModal(false)}
        candidates={candidates || []}
      />
    </div>
  )
}
