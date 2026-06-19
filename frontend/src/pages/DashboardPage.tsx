/**
 * Dashboard — overview of the resume profile and quick-access to all modules.
 */

import {
  BarChart3,
  BookOpen,
  Briefcase,
  CheckCircle2,
  MessageSquare,
  Star,
  Target,
  TrendingUp,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { resumeApi } from '../lib/api'
import type { AnalyzeResumeResponse } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'
import { FullPageLoader } from '../components/ui/LoadingSpinner'
import { ScoreRing } from '../components/ui/ScoreRing'

const moduleCards = [
  { to: '/ats', icon: Target, label: 'ATS Score', color: 'text-blue-400', bg: 'bg-blue-900/20 border-blue-800' },
  { to: '/skill-gap', icon: BookOpen, label: 'Skill Gap', color: 'text-purple-400', bg: 'bg-purple-900/20 border-purple-800' },
  { to: '/interview', icon: Star, label: 'Interview Prep', color: 'text-yellow-400', bg: 'bg-yellow-900/20 border-yellow-800' },
  { to: '/career', icon: TrendingUp, label: 'Career Paths', color: 'text-green-400', bg: 'bg-green-900/20 border-green-800' },
  { to: '/jobs', icon: Briefcase, label: 'Job Matches', color: 'text-orange-400', bg: 'bg-orange-900/20 border-orange-800' },
  { to: '/chat', icon: MessageSquare, label: 'AI Chat', color: 'text-indigo-400', bg: 'bg-indigo-900/20 border-indigo-800' },
]

export function DashboardPage() {
  const { state, dispatch } = useResumeStore()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  // Fetch analysis if not cached
  useEffect(() => {
    if (!state.resumeId || state.analysisResult) return

    const fetch = async () => {
      setLoading(true)
      try {
        const result = await resumeApi.analyzeResume(state.resumeId!)
        dispatch({ type: 'SET_ANALYSIS', result })
      } catch (e) {
        toast.error('Failed to load resume analysis')
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [state.resumeId])

  if (!state.resumeId) {
    navigate('/')
    return null
  }

  if (loading) return <FullPageLoader label="Analyzing your resume..." />

  const profile = state.profile
  const analysis = state.analysisResult

  return (
    <div className="animate-fade-in space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {profile?.name ? `Hi, ${profile.name.split(' ')[0]} 👋` : 'Your Dashboard'}
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            {profile?.summary
              ? profile.summary.slice(0, 120) + (profile.summary.length > 120 ? '...' : '')
              : 'Your resume has been processed and is ready for analysis.'}
          </p>
        </div>
        {analysis && (
          <ScoreRing
            score={analysis.overall_quality_score}
            size={100}
            label="Quality"
          />
        )}
      </div>

      {/* Profile at a glance */}
      {profile && (
        <div className="card">
          <h2 className="section-title">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            Profile Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Experience', value: profile.years_of_experience ? `${profile.years_of_experience} yrs` : 'N/A' },
              { label: 'Skills', value: `${profile.skills.length} skills` },
              { label: 'Education', value: profile.education[0]?.degree?.split(' ').slice(0, 2).join(' ') || 'N/A' },
              { label: 'Certifications', value: `${profile.certifications.length} certs` },
            ].map((stat) => (
              <div key={stat.label} className="bg-gray-800 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">{stat.label}</p>
                <p className="text-sm font-semibold text-white truncate">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* Top skills */}
          {profile.technical_skills.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Top Technical Skills</p>
              <div className="flex flex-wrap gap-2">
                {profile.technical_skills.slice(0, 12).map((skill) => (
                  <span key={skill} className="badge badge-blue">{skill}</span>
                ))}
                {profile.technical_skills.length > 12 && (
                  <span className="badge badge-blue">+{profile.technical_skills.length - 12} more</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analysis results */}
      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="section-title text-base">
              <CheckCircle2 className="w-4 h-4 text-green-400" />
              Strengths
            </h2>
            <ul className="space-y-2">
              {analysis.strengths.slice(0, 4).map((s, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h2 className="section-title text-base">
              <Target className="w-4 h-4 text-yellow-400" />
              Top Improvements
            </h2>
            <ul className="space-y-2">
              {analysis.improvements.slice(0, 4).map((s, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-yellow-400 mt-0.5">→</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Module navigation cards */}
      <div>
        <h2 className="section-title">
          <Briefcase className="w-5 h-5 text-indigo-400" />
          AI Analysis Modules
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {moduleCards.map((card) => (
            <button
              key={card.to}
              onClick={() => navigate(card.to)}
              className={`p-5 rounded-xl border text-left transition-all duration-150 hover:scale-[1.02] ${card.bg}`}
            >
              <card.icon className={`w-6 h-6 mb-3 ${card.color}`} />
              <p className="text-sm font-semibold text-gray-200">{card.label}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
