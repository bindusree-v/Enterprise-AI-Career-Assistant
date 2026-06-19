/**
 * Career Advisor — auto-populates from resume profile.
 * Shows career paths, trends, growth opportunities based entirely on the resume.
 */

import { TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { analysisApi, type CareerPath } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'
import { FullPageLoader } from '../components/ui/LoadingSpinner'

const GROWTH_COLORS: Record<string, string> = {
  high: 'badge-green', medium: 'badge-yellow', low: 'badge-red',
}

function CareerPathCard({ path }: { path: CareerPath }) {
  return (
    <div className="border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-3">
        <h3 className="font-semibold text-gray-100">{path.title}</h3>
        <span className={`badge ${GROWTH_COLORS[path.growth_potential] ?? 'badge-blue'} flex-shrink-0`}>
          {path.growth_potential} growth
        </span>
      </div>
      <p className="text-sm text-gray-400 mb-3">{path.description}</p>
      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        <div className="bg-gray-800 rounded-lg p-2">
          <span className="text-gray-500 text-xs">Timeline</span>
          <p className="text-gray-200 font-medium">{path.time_to_achieve}</p>
        </div>
        {path.average_salary && (
          <div className="bg-gray-800 rounded-lg p-2">
            <span className="text-gray-500 text-xs">Avg. Salary</span>
            <p className="text-gray-200 font-medium">{path.average_salary}</p>
          </div>
        )}
      </div>
      {path.required_skills.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 mb-1">Required Skills</p>
          <div className="flex flex-wrap gap-1">
            {path.required_skills.map((s, i) => <span key={i} className="badge badge-blue">{s}</span>)}
          </div>
        </div>
      )}
      {path.steps.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Steps to Get There</p>
          <ol className="space-y-1.5">
            {path.steps.map((step, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-400">
                <span className="text-indigo-400 font-medium flex-shrink-0">{i + 1}.</span>{step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

export function CareerPage() {
  const { state, dispatch } = useResumeStore()
  const { profile, jobContext } = state
  const [careerGoals, setCareerGoals] = useState('')
  const [loading, setLoading] = useState(false)
  const result = state.careerResult

  // Auto-derive current role from resume profile
  const detectedRole = profile?.experience?.[0]?.title ?? jobContext.targetRole ?? ''

  const handleAnalyze = async () => {
    setLoading(true)
    try {
      const data = await analysisApi.careerSuggestions({
        resumeId: state.resumeId!,
        currentRole: detectedRole || undefined,
        careerGoals: careerGoals || undefined,
        industryPreference: undefined,
        locationPreference: jobContext.location || undefined,
      })
      dispatch({ type: 'SET_CAREER', result: data })
      toast.success('Career analysis complete!')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <FullPageLoader label="Building your career roadmap..." />

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-green-400" />
          Career Advisor
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          AI-powered career paths based entirely on your resume profile.
        </p>
      </div>

      {/* Compact input — only career goals, everything else from resume */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2 p-3 bg-gray-800 rounded-lg">
          <span className="text-xs text-gray-500">Detected from your resume:</span>
          <span className="text-sm text-indigo-300 font-medium">
            {detectedRole || 'Professional profile'}
          </span>
          {profile?.years_of_experience && (
            <span className="badge badge-blue">{profile.years_of_experience} yrs exp</span>
          )}
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-1 block">
            Career Goals <span className="text-gray-600">(optional — leave blank for AI to decide)</span>
          </label>
          <textarea
            className="input resize-none min-h-[80px]"
            placeholder="e.g. 'Become a Senior AI Engineer in 3 years' or 'Transition into product management'"
            value={careerGoals}
            onChange={e => setCareerGoals(e.target.value)}
          />
        </div>
        <button className="btn-primary w-full md:w-auto px-8" onClick={handleAnalyze}>
          Get Career Advice
        </button>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="card">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Assessed Level</p>
            <p className="text-xl font-bold text-indigo-400">{result.current_level}</p>
          </div>

          <div>
            <h2 className="section-title">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Recommended Career Paths
            </h2>
            <div className="space-y-4">
              {result.career_paths.map((path, i) => <CareerPathCard key={i} path={path} />)}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="section-title text-base">📈 Industry Trends</h2>
              <ul className="space-y-2">
                {result.industry_trends.map((t, i) => (
                  <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-blue-400">•</span>{t}</li>
                ))}
              </ul>
            </div>
            <div className="card">
              <h2 className="section-title text-base">🌱 Growth Opportunities</h2>
              <ul className="space-y-2">
                {result.growth_opportunities.map((o, i) => (
                  <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-green-400">•</span>{o}</li>
                ))}
              </ul>
            </div>
            <div className="card">
              <h2 className="section-title text-base">✅ Action Plan</h2>
              <ol className="space-y-2">
                {result.action_plan.map((a, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-300">
                    <span className="text-indigo-400 font-medium">{i + 1}.</span>{a}
                  </li>
                ))}
              </ol>
            </div>
            <div className="card">
              <h2 className="section-title text-base">🤝 Networking Tips</h2>
              <ul className="space-y-2">
                {result.networking_tips.map((t, i) => (
                  <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-purple-400">•</span>{t}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
