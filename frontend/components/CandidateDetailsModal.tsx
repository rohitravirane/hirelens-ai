'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'

interface CandidateDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  candidateId: number | null
}

export default function CandidateDetailsModal({ isOpen, onClose, candidateId }: CandidateDetailsModalProps) {
  const [candidate, setCandidate] = useState<any>(null)
  const [resume, setResume] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

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

  if (!isOpen || !candidateId) return null

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
              {/* Contact Information */}
              <div className="mb-6 pt-4">
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

