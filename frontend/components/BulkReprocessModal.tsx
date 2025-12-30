'use client'

import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { useQueryClient } from 'react-query'

interface BulkReprocessModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: any[]
}

interface ProcessingStatus {
  resumeId: number
  fileName: string
  candidateName: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number
}

export default function BulkReprocessModal({ isOpen, onClose, candidates }: BulkReprocessModalProps) {
  const [processing, setProcessing] = useState<ProcessingStatus[]>([])
  const [isReprocessing, setIsReprocessing] = useState(false)
  const [completed, setCompleted] = useState(0)
  const [failed, setFailed] = useState(0)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (isOpen) {
      // Initialize processing status for all candidates with resumes
      const candidatesWithResumes = candidates.filter(c => c.resume_id && (c.resume_quality_score === null || c.resume_quality_score < 80))
      setProcessing(candidatesWithResumes.map(c => ({
        resumeId: c.resume_id,
        fileName: `Resume ${c.resume_id}`,
        candidateName: `${c.first_name} ${c.last_name}`,
        status: 'pending' as const,
      })))
      setCompleted(0)
      setFailed(0)
    }
  }, [isOpen, candidates])

  useEffect(() => {
    if (isReprocessing && processing.length > 0) {
      // Poll for status updates
      const interval = setInterval(() => {
        checkProcessingStatus()
      }, 2000) // Check every 2 seconds

      return () => clearInterval(interval)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isReprocessing])

  const checkProcessingStatus = async () => {
    const currentProcessing = processing
    const pendingOrProcessing = currentProcessing.filter(p => p.status === 'pending' || p.status === 'processing')
    
    if (pendingOrProcessing.length === 0) {
      setIsReprocessing(false)
      queryClient.invalidateQueries('candidates')
      queryClient.invalidateQueries('resumes')
      return
    }

    // Update statuses
    const updatedStatuses = await Promise.all(
      pendingOrProcessing.map(async (item) => {
        try {
          const response = await api.get(`/api/v1/resumes/${item.resumeId}`)
          const resume = response.data
          const newStatus = resume.processing_status === 'completed' ? 'completed' as const :
                         resume.processing_status === 'processing' ? 'processing' as const :
                         resume.processing_status === 'failed' ? 'failed' as const :
                         'processing' as const
          return { ...item, status: newStatus }
        } catch (err) {
          return { ...item, status: 'failed' as const }
        }
      })
    )

    // Update processing state
    const newProcessing = currentProcessing.map(p => {
      const updated = updatedStatuses.find(u => u.resumeId === p.resumeId)
      return updated || p
    })

    setProcessing(newProcessing)
    
    // Update counters
    const completedCount = newProcessing.filter(p => p.status === 'completed').length
    const failedCount = newProcessing.filter(p => p.status === 'failed').length
    setCompleted(completedCount)
    setFailed(failedCount)

    // Check if all done
    if (pendingOrProcessing.length === updatedStatuses.filter(u => u.status === 'completed' || u.status === 'failed').length) {
      setIsReprocessing(false)
      queryClient.invalidateQueries('candidates')
      queryClient.invalidateQueries('resumes')
    }
  }

  const handleBulkReprocess = async () => {
    const candidatesToReprocess = candidates.filter(c => c.resume_id && (c.resume_quality_score === null || c.resume_quality_score < 80))
    
    if (candidatesToReprocess.length === 0) {
      return
    }

    setIsReprocessing(true)
    setCompleted(0)
    setFailed(0)

    // Queue all reprocessing
    const promises = candidatesToReprocess.map(async (candidate) => {
      try {
        await api.post(`/api/v1/resumes/${candidate.resume_id}/reprocess`)
        // Update status to processing
        setProcessing(prev => prev.map(p => 
          p.resumeId === candidate.resume_id ? { ...p, status: 'processing' } : p
        ))
      } catch (err) {
        setProcessing(prev => prev.map(p => 
          p.resumeId === candidate.resume_id ? { ...p, status: 'failed' } : p
        ))
        setFailed(prev => prev + 1)
      }
    })

    await Promise.all(promises)

    // Start polling for status
    checkProcessingStatus()
  }

  if (!isOpen) return null

  const candidatesToReprocess = candidates.filter(c => c.resume_id && (c.resume_quality_score === null || c.resume_quality_score < 80))
  const total = candidatesToReprocess.length
  const allCompleted = completed + failed === total && total > 0

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        <div className="sticky top-0 bg-white z-10 border-b border-gray-200 px-6 pt-6 pb-4">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Bulk Reprocess Resumes</h2>
              <p className="text-sm text-gray-600 mt-1">
                {total} resume(s) with quality {'<'} 80% will be reprocessed
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {total === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">All resumes are up to date</h3>
              <p className="mt-2 text-sm text-gray-500">All resumes have quality score ≥ 80%</p>
            </div>
          ) : (
            <>
              {/* Progress Summary */}
              {isReprocessing && (
                <div className="mb-6 bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-blue-900">Processing Progress</span>
                    <span className="text-sm font-bold text-blue-700">
                      {completed + failed} / {total}
                    </span>
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-3 mb-2">
                    <div 
                      className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${((completed + failed) / total) * 100}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-blue-700">
                    <span>✅ Completed: {completed}</span>
                    <span>❌ Failed: {failed}</span>
                    <span>⏳ Processing: {total - completed - failed}</span>
                  </div>
                </div>
              )}

              {/* Processing List */}
              <div className="space-y-2">
                {processing.map((item, index) => (
                  <div 
                    key={item.resumeId} 
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className="flex-shrink-0">
                        {item.status === 'completed' ? (
                          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        ) : item.status === 'processing' ? (
                          <svg className="animate-spin w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647A7.962 7.962 0 0112 20c4.418 0 8-3.582 8-8h-4a4 4 0 11-8 0v4z"></path>
                          </svg>
                        ) : item.status === 'failed' ? (
                          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        ) : (
                          <div className="w-5 h-5 rounded-full border-2 border-gray-300"></div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{item.candidateName}</p>
                        <p className="text-xs text-gray-500">{item.fileName}</p>
                      </div>
                    </div>
                    <div className="flex-shrink-0 ml-4">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                        item.status === 'completed' ? 'bg-green-100 text-green-800' :
                        item.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                        item.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {item.status === 'completed' ? 'Completed' :
                         item.status === 'processing' ? 'Processing...' :
                         item.status === 'failed' ? 'Failed' :
                         'Pending'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Action Buttons */}
        <div className="border-t px-6 py-4 bg-gray-50">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              {allCompleted ? 'Close' : 'Cancel'}
            </button>
            {total > 0 && !isReprocessing && (
              <button
                onClick={handleBulkReprocess}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reprocess All ({total})
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

