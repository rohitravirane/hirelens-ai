'use client'

import { useState } from 'react'
import { useQuery } from 'react-query'
import api from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import Link from 'next/link'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)

  const { data: jobs, isLoading: jobsLoading } = useQuery(
    'jobs',
    async () => {
      const response = await api.get('/api/v1/jobs/', { params: { is_active: true } })
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
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Jobs Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Job Descriptions</h2>
              {jobsLoading ? (
                <div className="text-center py-4">Loading...</div>
              ) : (
                <div className="space-y-2">
                  {jobs?.map((job: any) => (
                    <button
                      key={job.id}
                      onClick={() => setSelectedJobId(job.id)}
                      className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                        selectedJobId === job.id
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="font-medium text-gray-900">{job.title}</div>
                      <div className="text-sm text-gray-500">{job.company}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Rankings Main Content */}
          <div className="lg:col-span-2">
            {selectedJobId ? (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                  <h2 className="text-xl font-semibold">Candidate Rankings</h2>
                </div>
                {rankingsLoading ? (
                  <div className="text-center py-12">Loading rankings...</div>
                ) : (
                  <div className="divide-y">
                    {rankings?.map((ranking: any, index: number) => (
                      <div key={ranking.candidate_id} className="p-6 hover:bg-gray-50">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-2xl font-bold text-gray-400">
                                #{index + 1}
                              </span>
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900">
                                  {ranking.candidate_name || 'Unknown Candidate'}
                                </h3>
                                <p className="text-sm text-gray-500">
                                  {ranking.candidate_email}
                                </p>
                              </div>
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
                                {ranking.match_result.confidence_level.toUpperCase()}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* AI Explanation */}
                        {ranking.match_result.ai_explanation && (
                          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                            <h4 className="font-semibold text-sm text-gray-700 mb-2">
                              AI Analysis
                            </h4>
                            <p className="text-sm text-gray-600 mb-3">
                              {ranking.match_result.ai_explanation.summary}
                            </p>
                            {ranking.match_result.ai_explanation.strengths && (
                              <div className="mb-2">
                                <span className="text-xs font-semibold text-green-700">
                                  Strengths:
                                </span>
                                <ul className="list-disc list-inside text-xs text-gray-600 ml-2">
                                  {ranking.match_result.ai_explanation.strengths
                                    .slice(0, 3)
                                    .map((strength: string, i: number) => (
                                      <li key={i}>{strength}</li>
                                    ))}
                                </ul>
                              </div>
                            )}
                            {ranking.match_result.ai_explanation.weaknesses && (
                              <div>
                                <span className="text-xs font-semibold text-red-700">
                                  Gaps:
                                </span>
                                <ul className="list-disc list-inside text-xs text-gray-600 ml-2">
                                  {ranking.match_result.ai_explanation.weaknesses
                                    .slice(0, 2)
                                    .map((weakness: string, i: number) => (
                                      <li key={i}>{weakness}</li>
                                    ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Score Breakdown */}
                        <div className="mt-4 grid grid-cols-4 gap-2 text-xs">
                          <div>
                            <div className="text-gray-500">Skills</div>
                            <div className="font-semibold">
                              {ranking.match_result.skill_match_score.toFixed(0)}
                            </div>
                          </div>
                          <div>
                            <div className="text-gray-500">Experience</div>
                            <div className="font-semibold">
                              {ranking.match_result.experience_score.toFixed(0)}
                            </div>
                          </div>
                          <div>
                            <div className="text-gray-500">Projects</div>
                            <div className="font-semibold">
                              {ranking.match_result.project_similarity_score.toFixed(0)}
                            </div>
                          </div>
                          <div>
                            <div className="text-gray-500">Domain</div>
                            <div className="font-semibold">
                              {ranking.match_result.domain_familiarity_score.toFixed(0)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <p className="text-gray-500">Select a job to view candidate rankings</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

