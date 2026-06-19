/**
 * Upload page — step-by-step resume onboarding with drag-and-drop.
 */

import { clsx } from 'clsx'
import { CheckCircle2, FileText, Loader2, Upload, Zap } from 'lucide-react'
import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { usePipeline } from '../hooks/usePipeline'

const STEPS = [
  { id: 'uploading', label: 'Uploading file', icon: Upload },
  { id: 'extracting', label: 'Extracting & parsing resume', icon: FileText },
  { id: 'embedding', label: 'Generating AI embeddings', icon: Zap },
  { id: 'ready', label: 'Ready for analysis', icon: CheckCircle2 },
]

export function UploadPage() {
  const { state, runPipeline } = usePipeline()
  const navigate = useNavigate()
  const isProcessing = ['uploading', 'extracting', 'embedding'].includes(state.pipelineStep)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return
      const file = acceptedFiles[0]
      await runPipeline(file)
    },
    [runPipeline]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isProcessing,
  })

  // Auto-navigate to dashboard when ready
  if (state.pipelineStep === 'ready') {
    setTimeout(() => navigate('/dashboard'), 800)
  }

  const currentStepIndex = STEPS.findIndex((s) => s.id === state.pipelineStep)

  return (
    <div className="max-w-2xl mx-auto py-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Welcome to <span className="text-indigo-400">CareerGPT</span>
        </h1>
        <p className="text-gray-400">
          Upload your resume to unlock AI-powered career insights, ATS scoring, skill gap analysis, and more.
        </p>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer',
          isDragActive
            ? 'border-indigo-400 bg-indigo-900/20'
            : isProcessing
            ? 'border-gray-700 bg-gray-900 cursor-not-allowed'
            : 'border-gray-700 bg-gray-900 hover:border-indigo-600 hover:bg-indigo-900/10'
        )}
      >
        <input {...getInputProps()} />

        {isProcessing ? (
          <Loader2 className="w-12 h-12 text-indigo-400 mx-auto mb-4 animate-spin" />
        ) : (
          <Upload
            className={clsx(
              'w-12 h-12 mx-auto mb-4',
              isDragActive ? 'text-indigo-400' : 'text-gray-500'
            )}
          />
        )}

        <p className="text-lg font-medium text-gray-200 mb-1">
          {isDragActive
            ? 'Drop your resume here'
            : isProcessing
            ? 'Processing your resume...'
            : 'Drop your resume PDF here'}
        </p>
        <p className="text-sm text-gray-500">
          {isProcessing ? 'This may take 30–60 seconds' : 'or click to browse — PDF only, max 10MB'}
        </p>
      </div>

      {/* Pipeline progress */}
      {state.pipelineStep !== 'idle' && state.pipelineStep !== 'error' && (
        <div className="mt-8 card animate-fade-in">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wide">
            Processing Pipeline
          </h3>
          <div className="space-y-3">
            {STEPS.map((step, idx) => {
              const isDone = idx < currentStepIndex || state.pipelineStep === 'ready'
              const isActive = step.id === state.pipelineStep
              const isPending = idx > currentStepIndex && state.pipelineStep !== 'ready'

              return (
                <div key={step.id} className="flex items-center gap-3">
                  <div
                    className={clsx(
                      'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-colors',
                      isDone
                        ? 'bg-green-600'
                        : isActive
                        ? 'bg-indigo-600 animate-pulse'
                        : 'bg-gray-800'
                    )}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    ) : isActive ? (
                      <Loader2 className="w-4 h-4 text-white animate-spin" />
                    ) : (
                      <step.icon className="w-4 h-4 text-gray-600" />
                    )}
                  </div>
                  <span
                    className={clsx(
                      'text-sm',
                      isDone ? 'text-green-400' : isActive ? 'text-white font-medium' : 'text-gray-600'
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Error state */}
      {state.pipelineStep === 'error' && (
        <div className="mt-6 p-4 bg-red-900/20 border border-red-700 rounded-xl animate-fade-in">
          <p className="text-red-400 text-sm font-medium">⚠ {state.pipelineError}</p>
          <p className="text-gray-500 text-xs mt-1">Please try uploading your resume again.</p>
        </div>
      )}

      {/* Feature highlights */}
      {state.pipelineStep === 'idle' && (
        <div className="mt-10 grid grid-cols-2 gap-4 animate-fade-in">
          {[
            { emoji: '🎯', title: 'ATS Scoring', desc: 'See how you score against any job description' },
            { emoji: '📊', title: 'Skill Gap Analysis', desc: 'Know exactly what to learn next' },
            { emoji: '💬', title: 'Interview Prep', desc: 'Personalized questions from your resume' },
            { emoji: '🚀', title: 'Career Paths', desc: 'AI-guided career progression roadmaps' },
          ].map((f) => (
            <div key={f.title} className="card p-4">
              <span className="text-2xl">{f.emoji}</span>
              <h4 className="text-sm font-semibold text-gray-200 mt-2">{f.title}</h4>
              <p className="text-xs text-gray-500 mt-1">{f.desc}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
