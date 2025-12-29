'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import JobModal from '@/components/JobModal'
import ResumeUpload from '@/components/ResumeUpload'
import CandidateModal from '@/components/CandidateModal'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const queryClient = useQueryClient()
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [showJobModal, setShowJobModal] = useState(false)
  const [showResumeModal, setShowResumeModal] = useState(false)
  const [showCandidateModal, setShowCandidateModal] = useState(false)
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<'jobs' | 'candidates' | 'rankings'>('jobs')

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

  const { data: resumes, isLoading: resumesLoading } = useQuery(
    'resumes',
    async () => {
      const response = await api.get('/api/v1/resumes/')
      return response.data
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
      return api.post(`/api/v1/matching/match?candidate_id=${candidateId}&job_id=${jobId}`)
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['rankings', selectedJobId])
        queryClient.invalidateQueries('candidates')
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
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">HireLens AI</h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={logout}
              className="text-sm text-primary-600 hover:text-primary-700 px-3 py-1 rounded hover:bg-gray-100"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('jobs')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'jobs'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Jobs
              </button>
              <button
                onClick={() => setActiveTab('candidates')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'candidates'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Candidates
              </button>
              <button
                onClick={() => setActiveTab('rankings')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
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
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Job Descriptions</h2>
              <button
                onClick={() => setShowJobModal(true)}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 flex items-center space-x-2"
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
                    className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => {
                      setSelectedJobId(job.id)
                      setActiveTab('rankings')
                    }}
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
                    <div className="mt-4 pt-4 border-t">
                      <span className="text-xs text-gray-500">
                        Created: {new Date(job.created_at).toLocaleDateString()}
                      </span>
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
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Candidates</h2>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowResumeModal(true)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center space-x-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span>Upload Resume</span>
                </button>
                <button
                  onClick={() => setShowCandidateModal(true)}
                  className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 flex items-center space-x-2"
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
              <div className="bg-white rounded-lg shadow overflow-hidden">
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
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            candidate.status === 'active' ? 'bg-green-100 text-green-800' :
                            candidate.status === 'shortlisted' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {candidate.status || 'active'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {selectedJobId && (
                            <button
                              onClick={() => matchMutation.mutate({ candidateId: candidate.id, jobId: selectedJobId })}
                              disabled={matchMutation.isLoading}
                              className="text-primary-600 hover:text-primary-900"
                            >
                              Match
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Candidate Rankings</h2>
                {selectedJobId && jobs && (
                  <p className="text-sm text-gray-500 mt-1">
                    {jobs.find((j: any) => j.id === selectedJobId)?.title} - {jobs.find((j: any) => j.id === selectedJobId)?.company}
                  </p>
                )}
              </div>
              <div className="flex space-x-3">
                {selectedJobId && candidates && candidates.length > 0 && (
                  <button
                    onClick={handleMatchAll}
                    disabled={bulkMatchMutation.isLoading}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>{bulkMatchMutation.isLoading ? 'Matching...' : 'Match All Candidates'}</span>
                  </button>
                )}
                <select
                  value={selectedJobId || ''}
                  onChange={(e) => setSelectedJobId(e.target.value ? parseInt(e.target.value) : null)}
                  className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Select a job</option>
                  {jobs?.map((job: any) => (
                    <option key={job.id} value={job.id}>
                      {job.title} - {job.company}
                    </option>
                  ))}
                </select>
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
                        <div className="grid grid-cols-2 gap-4">
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
                    <div className="mt-4 grid grid-cols-4 gap-4">
                      <div className="text-center p-3 bg-blue-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Skills</div>
                        <div className="text-lg font-semibold text-blue-700">
                          {ranking.match_result.skill_match_score?.toFixed(0) || '0'}
                        </div>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Experience</div>
                        <div className="text-lg font-semibold text-green-700">
                          {ranking.match_result.experience_score?.toFixed(0) || '0'}
                        </div>
                      </div>
                      <div className="text-center p-3 bg-purple-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Projects</div>
                        <div className="text-lg font-semibold text-purple-700">
                          {ranking.match_result.project_similarity_score?.toFixed(0) || '0'}
                        </div>
                      </div>
                      <div className="text-center p-3 bg-orange-50 rounded">
                        <div className="text-xs text-gray-500 mb-1">Domain</div>
                        <div className="text-lg font-semibold text-orange-700">
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
    </div>
  )
}
