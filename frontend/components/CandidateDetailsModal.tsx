'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { useQueryClient } from 'react-query'

interface CandidateDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  candidateId: number | null
}

export default function CandidateDetailsModal({ isOpen, onClose, candidateId }: CandidateDetailsModalProps) {
  const [candidate, setCandidate] = useState<any>(null)
  const [resume, setResume] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [reprocessing, setReprocessing] = useState(false)
  const [error, setError] = useState('')
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (isOpen && candidateId) {
      fetchCandidateDetails()
    }
  }, [isOpen, candidateId])

  const fetchCandidateDetails = async () => {
    if (!candidateId) return
    
    setLoading(true)
    setError('')
    try {
      // Fetch candidate details
      const candidateResponse = await api.get(`/api/v1/candidates/${candidateId}`)
      setCandidate(candidateResponse.data)
      
      // If candidate has a resume, fetch resume details
      if (candidateResponse.data.resume_id) {
        try {
          const resumeResponse = await api.get(`/api/v1/resumes/${candidateResponse.data.resume_id}`)
          setResume(resumeResponse.data)
        } catch (resumeErr) {
          console.error('Failed to fetch resume:', resumeErr)
          // Don't fail the whole modal if resume fetch fails
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load candidate details')
    } finally {
      setLoading(false)
    }
  }

  const handleReprocess = async () => {
    if (!candidate?.resume_id) return
    
    setReprocessing(true)
    setError('')
    try {
      await api.post(`/api/v1/resumes/${candidate.resume_id}/reprocess`)
      setNotification({ 
        type: 'success', 
        message: 'Resume queued for reprocessing. Quality score will update in a few minutes.' 
      })
      // Refresh candidate data after a delay
      setTimeout(() => {
        fetchCandidateDetails()
        queryClient.invalidateQueries('candidates')
      }, 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reprocess resume')
    } finally {
      setReprocessing(false)
    }
  }

  if (!isOpen || !candidateId) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      {/* Notification Toast */}
      {notification && (
        <div className="fixed top-4 right-4 left-4 sm:left-auto z-[60] animate-slide-in">
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
      
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700 m-6">
            {error}
          </div>
        ) : candidate ? (
          <>
            {/* Sticky Header */}
            <div className="sticky top-0 bg-white z-10 border-b border-gray-200 px-6 pt-6 pb-4">
              <div className="flex justify-between items-start">
                <div className="flex-1 pr-4">
                  <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                    {candidate.first_name} {candidate.last_name}
                  </h2>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                    {candidate.email && (
                      <span className="font-medium">{candidate.email}</span>
                    )}
                    {candidate.phone && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span>{candidate.phone}</span>
                      </>
                    )}
                    {candidate.status && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          candidate.status === 'active' ? 'bg-green-100 text-green-800' :
                          candidate.status === 'shortlisted' ? 'bg-blue-100 text-blue-800' :
                          candidate.status === 'interview' ? 'bg-yellow-100 text-yellow-800' :
                          candidate.status === 'offer' ? 'bg-purple-100 text-purple-800' :
                          candidate.status === 'rejected' ? 'bg-red-100 text-red-800' :
                          candidate.status === 'hired' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {candidate.status}
                        </span>
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
            <div className="flex-1 overflow-y-auto px-6">
              {/* Quality Score Indicator */}
              {candidate.resume_quality_score !== null && candidate.resume_quality_score !== undefined && (
                <div className="mb-6 pt-4">
                  <div className="bg-gray-50 rounded-lg p-4 border-2 border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-semibold text-gray-900">Resume Quality Score</h3>
                      <span className={`text-lg font-bold ${
                        candidate.resume_quality_score >= 80 ? 'text-green-600' :
                        candidate.resume_quality_score >= 50 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {candidate.resume_quality_score}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                      <div 
                        className={`h-3 rounded-full transition-all ${
                          candidate.resume_quality_score >= 80 ? 'bg-green-500' :
                          candidate.resume_quality_score >= 50 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${candidate.resume_quality_score}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className={`text-xs ${
                        candidate.resume_quality_score >= 80 ? 'text-green-700' :
                        candidate.resume_quality_score >= 50 ? 'text-yellow-700' :
                        'text-red-700'
                      }`}>
                        {candidate.resume_quality_score >= 80 ? '✅ Excellent - Ready for matching' :
                         candidate.resume_quality_score >= 50 ? '⚠️ Moderate - Reprocessing recommended' :
                         '❌ Poor - Reprocessing required'}
                      </p>
                      {candidate.resume_quality_score < 80 && candidate.resume_id && (
                        <button
                          onClick={handleReprocess}
                          disabled={reprocessing}
                          className="px-3 py-1 text-xs font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                        >
                          {reprocessing ? (
                            <>
                              <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647A7.962 7.962 0 0112 20c4.418 0 8-3.582 8-8h-4a4 4 0 11-8 0v4z"></path>
                              </svg>
                              Processing...
                            </>
                          ) : (
                            <>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                              </svg>
                              Reprocess
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Contact Information */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Contact Information</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {candidate.email && (
                    <div>
                      <span className="text-xs text-gray-500">Email</span>
                      <p className="text-sm text-gray-900 mt-1">{candidate.email}</p>
                    </div>
                  )}
                  {candidate.phone && (
                    <div>
                      <span className="text-xs text-gray-500">Phone</span>
                      <p className="text-sm text-gray-900 mt-1">{candidate.phone}</p>
                    </div>
                  )}
                  {candidate.linkedin_url && (
                    <div>
                      <span className="text-xs text-gray-500">LinkedIn</span>
                      <a 
                        href={candidate.linkedin_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-primary-600 hover:text-primary-700 mt-1 block truncate"
                      >
                        {candidate.linkedin_url}
                      </a>
                    </div>
                  )}
                  {candidate.portfolio_url && (
                    <div>
                      <span className="text-xs text-gray-500">Portfolio</span>
                      <a 
                        href={candidate.portfolio_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-primary-600 hover:text-primary-700 mt-1 block truncate"
                      >
                        {candidate.portfolio_url}
                      </a>
                    </div>
                  )}
                </div>
              </div>

              {/* Resume Information */}
              {resume && resume.latest_version && (
                <>
                  {/* Skills */}
                  {resume.latest_version.skills && resume.latest_version.skills.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Skills</h3>
                      <div className="flex flex-wrap gap-2">
                        {resume.latest_version.skills.map((skill: string, i: number) => (
                          <span
                            key={i}
                            className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Experience */}
                  {resume.latest_version.experience_years !== null && resume.latest_version.experience_years !== undefined && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Experience</h3>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <p className="text-2xl font-bold text-primary-600">
                          {resume.latest_version.experience_years} {resume.latest_version.experience_years === 1 ? 'Year' : 'Years'}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">Total Experience</p>
                      </div>
                    </div>
                  )}

                  {/* Experience Details */}
                  {resume.latest_version.experience && resume.latest_version.experience.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Work Experience</h3>
                      <div className="space-y-4">
                        {resume.latest_version.experience.map((exp: any, i: number) => (
                          <div key={i} className="bg-gray-50 rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h4 className="font-semibold text-gray-900">{exp.title || exp.position || 'N/A'}</h4>
                                <p className="text-sm text-gray-600">{exp.company || exp.organization || 'N/A'}</p>
                              </div>
                              {(exp.start_date || exp.end_date) && (
                                <span className="text-xs text-gray-500 whitespace-nowrap">
                                  {exp.start_date || 'N/A'} - {exp.end_date || 'Present'}
                                </span>
                              )}
                            </div>
                            {exp.description && (
                              <p className="text-sm text-gray-700 mt-2">{exp.description}</p>
                            )}
                            {exp.location && (
                              <p className="text-xs text-gray-500 mt-1">{exp.location}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Education */}
                  {resume.latest_version.education && resume.latest_version.education.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Education</h3>
                      <div className="space-y-3">
                        {resume.latest_version.education.map((edu: any, i: number) => (
                          <div key={i} className="bg-gray-50 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-900">{edu.degree || edu.qualification || 'N/A'}</h4>
                            <p className="text-sm text-gray-600">{edu.institution || edu.school || edu.university || 'N/A'}</p>
                            {(edu.graduation_date || edu.year) && (
                              <p className="text-xs text-gray-500 mt-1">
                                {edu.graduation_date || edu.year || 'N/A'}
                              </p>
                            )}
                            {edu.field_of_study && (
                              <p className="text-sm text-gray-700 mt-1">{edu.field_of_study}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Projects */}
                  {resume.latest_version.projects && resume.latest_version.projects.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Projects</h3>
                      <div className="space-y-3">
                        {resume.latest_version.projects.map((project: any, i: number) => (
                          <div key={i} className="bg-gray-50 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-900">{project.name || project.title || 'N/A'}</h4>
                            {project.description && (
                              <p className="text-sm text-gray-700 mt-1">{project.description}</p>
                            )}
                            {project.technologies && Array.isArray(project.technologies) && project.technologies.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {project.technologies.map((tech: string, j: number) => (
                                  <span key={j} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                                    {tech}
                                  </span>
                                ))}
                              </div>
                            )}
                            {project.url && (
                              <a 
                                href={project.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-xs text-primary-600 hover:text-primary-700 mt-2 inline-block"
                              >
                                View Project →
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resume Raw Text */}
                  {resume.raw_text && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Resume Text</h3>
                      <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                          {resume.raw_text}
                        </pre>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Notes */}
              {candidate.notes && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Notes</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{candidate.notes}</p>
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="pt-4 border-t text-xs text-gray-500 pb-6">
                <p>Created: {new Date(candidate.created_at).toLocaleString()}</p>
                {resume && (
                  <p className="mt-1">Resume: {resume.file_name} ({resume.processing_status})</p>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="border-t px-6 py-4 bg-gray-50">
              <button
                onClick={onClose}
                className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
              >
                Close
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

