/**
 * Job Recommendations page — AI-matched job opportunities with match scores.
 */

import { Briefcase, Building2, MapPin, Wifi } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { analysisApi } from '../lib/api'
import type { JobMatch } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'
import { FullPageLoader } from '../components/ui/LoadingSpinner'
import { ScoreRing } from '../components/ui/ScoreRing'

function JobCard({ job }: { job: JobMatch }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-100 text-base">{job.title}</h3>
          <div className="flex items-center gap-3 mt-1 text-sm text-gray-400">
            <span className="flex items-center gap-1">
              <Building2 className="w-3 h-3" />
              {job.company}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {job.location}
            </span>
            {job.remote && (
              <span className="flex items-center gap-1 text-green-400">
                <Wifi className="w-3 h-3" />
                Remote
              </span>
            )}
          </div>
        </div>
        <ScoreRing score={job.match_percentage} size={72} label="Match" />
      </div>

      <div className="flex gap-3 mb-3 flex-wrap">
        <span className="badge badge-blue">{job.job_type}</span>
        {job.salary_range && (
          <span className="text-sm text-gray-400">💰 {job.salary_range}</span>
        )}
      </div>

      <p className="text-sm text-gray-400 italic mb-3">"{job.why_good_fit}"</p>

      <div className="grid grid-cols-2 gap-3 text-sm mb-3">
        <div>
          <p className="text-xs text-gray-500 mb-1">Matching Skills</p>
          <div className="flex flex-wrap gap-1">
            {job.matching_skills.slice(0, 4).map((s, i) => (
              <span key={i} className="badge badge-green">{s}</span>
            ))}
            {job.matching_skills.length > 4 && (
              <span className="badge badge-green">+{job.matching_skills.length - 4}</span>
            )}
          </div>
        </div>
        {job.missing_skills.length > 0 && (
          <div>
            <p className="text-xs text-gray-500 mb-1">Skills to Develop</p>
            <div className="flex flex-wrap gap-1">
              {job.missing_skills.slice(0, 3).map((s, i) => (
                <span key={i} className="badge badge-red">{s}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {job.apply_url && (
        <a
          href={job.apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary inline-block text-center text-sm mt-2"
        >
          Apply Now →
        </a>
      )}
    </div>
  )
}

export function JobsPage() {
  const { state, dispatch } = useResumeStore()
  const [targetRole, setTargetRole] = useState('')
  const [location, setLocation] = useState('')
  const [remotePreference, setRemotePreference] = useState('any')
  const [experienceLevel, setExperienceLevel] = useState('mid')
  const [loading, setLoading] = useState(false)
  const result = state.jobResult

  const handleSearch = async () => {
    setLoading(true)
    try {
      const data = await analysisApi.jobRecommendations({
        resumeId: state.resumeId!,
        targetRole: targetRole || undefined,
        location: location || undefined,
        remotePreference,
        experienceLevel,
      })
      dispatch({ type: 'SET_JOBS', result: data })
      toast.success(`Found ${data.total_matches} job matches!`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <FullPageLoader label="Finding your best job matches..." />

  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Briefcase className="w-6 h-6 text-orange-400" />
          Job Recommendations
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          AI-curated job matches with honest compatibility scores and reasoning.
        </p>
      </div>

      <div className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Target Role</label>
            <input
              className="input"
              placeholder="e.g. Senior Data Scientist"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Location</label>
            <input
              className="input"
              placeholder="e.g. New York, London, or Remote"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Remote Preference</label>
            <select className="input" value={remotePreference} onChange={(e) => setRemotePreference(e.target.value)}>
              <option value="any">Any</option>
              <option value="remote">Remote Only</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site Only</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Experience Level</label>
            <select className="input" value={experienceLevel} onChange={(e) => setExperienceLevel(e.target.value)}>
              <option value="junior">Junior</option>
              <option value="mid">Mid-level</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead / Principal</option>
            </select>
          </div>
        </div>
        <button className="btn-primary" onClick={handleSearch}>
          Find My Job Matches
        </button>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">
              {result.total_matches} Job Matches
            </h2>
          </div>

          <div className="space-y-4">
            {result.jobs.map((job, i) => (
              <JobCard key={i} job={job} />
            ))}
          </div>

          {result.search_strategy.length > 0 && (
            <div className="card">
              <h2 className="section-title">🔍 Job Search Strategy</h2>
              <ul className="space-y-2">
                {result.search_strategy.map((s, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-300">
                    <span className="text-indigo-400 font-medium">{i + 1}.</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
