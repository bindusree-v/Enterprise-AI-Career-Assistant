/**
 * ATS Score — uses shared job context (role + JD set once in JobContextPanel).
 * No repeated input fields.
 */

import { AlertCircle, CheckCircle2, Target, XCircle } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { analysisApi } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'
import { JobContextPanel } from '../components/ui/JobContextPanel'
import { FullPageLoader } from '../components/ui/LoadingSpinner'
import { ProgressBar } from '../components/ui/ProgressBar'
import { ScoreRing } from '../components/ui/ScoreRing'

export function ATSPage() {
  const { state, dispatch } = useResumeStore()
  const { jobContext } = state
  const [loading, setLoading] = useState(false)
  const result = state.atsResult

  const handleAnalyze = async () => {
    if (!jobContext.targetRole) {
      toast.error('Set your Target Role in the Job Context panel above')
      return
    }
    if (!jobContext.jobDescription || jobContext.jobDescription.length < 50) {
      toast.error('Paste a job description (min 50 characters) in the Job Context panel')
      return
    }
    setLoading(true)
    try {
      const data = await analysisApi.atsScore(
        state.resumeId!,
        jobContext.jobDescription,
        jobContext.targetRole,
      )
      dispatch({ type: 'SET_ATS', result: data })
      toast.success('ATS analysis complete!')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'ATS analysis failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <FullPageLoader label="Analyzing ATS compatibility..." />

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Target className="w-6 h-6 text-blue-400" />
          ATS Score Analyzer
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Score your resume against the job description for ATS compatibility.
        </p>
      </div>

      {/* Shared job context — entered once */}
      <JobContextPanel />

      <button
        className="btn-primary w-full md:w-auto px-8"
        onClick={handleAnalyze}
        disabled={!jobContext.targetRole || !jobContext.jobDescription}
      >
        Analyze ATS Compatibility
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="card">
            <h2 className="section-title">Overall Compatibility</h2>
            <div className="flex items-center gap-8 flex-wrap">
              <ScoreRing score={result.overall_score} size={120} label="Overall" />
              <div className="flex-1 space-y-3 min-w-[200px]">
                <ProgressBar value={result.keyword_match_score} label="Keyword Match" />
                <ProgressBar value={result.content_score} label="Content Quality" />
                <ProgressBar value={result.format_score} label="ATS Formatting" />
              </div>
            </div>
            <p className="mt-4 text-sm text-gray-400 border-t border-gray-800 pt-4">{result.summary}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="section-title text-base">
                <CheckCircle2 className="w-4 h-4 text-green-400" />
                Keywords Found ({result.keywords_found.length})
              </h2>
              <div className="flex flex-wrap gap-2">
                {result.keywords_found.map(kw => <span key={kw} className="badge badge-green">{kw}</span>)}
              </div>
            </div>
            <div className="card">
              <h2 className="section-title text-base">
                <XCircle className="w-4 h-4 text-red-400" />
                Missing Keywords ({result.keywords_missing.length})
              </h2>
              <div className="flex flex-wrap gap-2">
                {result.keywords_missing.map(kw => <span key={kw} className="badge badge-red">{kw}</span>)}
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="section-title">
              <AlertCircle className="w-5 h-5 text-yellow-400" />
              Optimization Recommendations
            </h2>
            <ul className="space-y-3">
              {result.recommendations.map((rec, i) => (
                <li key={i} className="flex gap-3 text-sm text-gray-300">
                  <span className="text-yellow-400 font-bold flex-shrink-0">{i + 1}.</span>{rec}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
