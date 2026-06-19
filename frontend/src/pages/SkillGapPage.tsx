/**
 * Skill Gap Analysis — uses shared job context automatically.
 */

import { BookOpen, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { analysisApi, type SkillGap } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'
import { JobContextPanel } from '../components/ui/JobContextPanel'
import { FullPageLoader } from '../components/ui/LoadingSpinner'

const PRIORITY_COLORS: Record<string, string> = {
  high: 'badge-red', medium: 'badge-yellow', low: 'badge-blue',
}

function SkillGapCard({ gap }: { gap: SkillGap }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-800/50"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-center gap-3">
          <span className={`badge ${PRIORITY_COLORS[gap.priority] ?? 'badge-blue'}`}>{gap.priority}</span>
          <span className="font-medium text-gray-200">{gap.skill}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-500">{gap.current_level} → {gap.required_level}</span>
          {open ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
        </div>
      </button>
      {open && (
        <div className="px-4 pb-4 border-t border-gray-800 pt-3 space-y-2 animate-fade-in">
          {gap.learning_resources.map((res, i) => (
            <div key={i} className="flex items-start gap-3 bg-gray-800 rounded-lg p-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-200">{res.name}</span>
                  {res.url && (
                    <a href={res.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-3 h-3 text-indigo-400" />
                    </a>
                  )}
                </div>
                <div className="flex gap-3 text-xs text-gray-500">
                  <span className="badge badge-purple">{res.type}</span>
                  {res.duration && <span>⏱ {res.duration}</span>}
                  {res.cost && <span>💰 {res.cost}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function SkillGapPage() {
  const { state, dispatch } = useResumeStore()
  const { jobContext } = state
  const [loading, setLoading] = useState(false)
  const result = state.skillGapResult

  const handleAnalyze = async () => {
    if (!jobContext.targetRole) {
      toast.error('Set your Target Role in the Job Context panel above')
      return
    }
    setLoading(true)
    try {
      const data = await analysisApi.skillGap(
        state.resumeId!,
        jobContext.targetRole,
        jobContext.jobDescription || undefined,
        jobContext.experienceLevel,
      )
      dispatch({ type: 'SET_SKILL_GAP', result: data })
      toast.success('Skill gap analysis complete!')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <FullPageLoader label="Analyzing skill gaps..." />

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-purple-400" />
          Skill Gap Analysis
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Compare your resume skills against the target role requirements.
        </p>
      </div>

      <JobContextPanel />

      <button
        className="btn-primary w-full md:w-auto px-8"
        onClick={handleAnalyze}
        disabled={!jobContext.targetRole}
      >
        Analyze Skill Gap
      </button>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="card">
            <h2 className="section-title">Analysis for: {result.target_role}</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-green-900/20 border border-green-800 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Skills You Have</p>
                <p className="text-2xl font-bold text-green-400">{result.current_skills.length}</p>
              </div>
              <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Skill Gaps</p>
                <p className="text-2xl font-bold text-red-400">{result.skill_gaps.length}</p>
              </div>
              <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Time to Ready</p>
                <p className="text-lg font-bold text-blue-400">{result.estimated_time_to_ready}</p>
              </div>
            </div>
          </div>

          {result.strengths.length > 0 && (
            <div className="card">
              <h2 className="section-title">💪 Your Strengths</h2>
              <div className="flex flex-wrap gap-2">
                {result.strengths.map((s, i) => <span key={i} className="badge badge-green">{s}</span>)}
              </div>
            </div>
          )}

          {result.skill_gaps.length > 0 && (
            <div className="card">
              <h2 className="section-title">📈 Skill Gaps to Address</h2>
              <div className="space-y-3">
                {result.skill_gaps.map((gap, i) => <SkillGapCard key={i} gap={gap} />)}
              </div>
            </div>
          )}

          {result.roadmap.length > 0 && (
            <div className="card">
              <h2 className="section-title">🗺️ Learning Roadmap</h2>
              <ol className="space-y-3">
                {result.roadmap.map((step, i) => (
                  <li key={i} className="flex gap-3 text-sm text-gray-300">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-600/20 border border-indigo-600/40 flex items-center justify-center text-indigo-400 text-xs font-bold">
                      {i + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {result.certifications_recommended.length > 0 && (
            <div className="card">
              <h2 className="section-title">🏆 Recommended Certifications</h2>
              <div className="flex flex-wrap gap-2">
                {result.certifications_recommended.map((cert, i) => (
                  <span key={i} className="badge badge-purple">{cert}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
