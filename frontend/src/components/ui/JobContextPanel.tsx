/**
 * JobContextPanel — enter Target Role + Job Description ONCE.
 * This data flows to ATS, Skill Gap, Interview Prep, and Job Matches automatically.
 * Lives in the store so it persists across page navigation.
 */

import { CheckCircle2, ChevronDown, ChevronUp, Pencil } from 'lucide-react'
import { useState } from 'react'
import { useResumeStore } from '../../store/resumeStore'

export function JobContextPanel() {
  const { state, dispatch } = useResumeStore()
  const { jobContext } = state
  const [expanded, setExpanded] = useState(!jobContext.targetRole)

  const isSet = !!jobContext.targetRole

  const update = (field: string, value: string) =>
    dispatch({ type: 'SET_JOB_CONTEXT', context: { [field]: value } })

  return (
    <div className={`border rounded-xl overflow-hidden mb-6 ${isSet ? 'border-green-800 bg-green-900/10' : 'border-indigo-700 bg-indigo-900/10'}`}>
      {/* Header */}
      <button
        className="w-full flex items-center justify-between px-5 py-3 text-left"
        onClick={() => setExpanded(o => !o)}
      >
        <div className="flex items-center gap-2">
          {isSet
            ? <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
            : <Pencil className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          }
          <span className="text-sm font-semibold text-gray-200">
            {isSet
              ? `Job Context: ${jobContext.targetRole}`
              : 'Set Target Role & Job Description (used by all sections)'}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {isSet && (
            <span className="badge badge-green text-xs">Shared across all sections</span>
          )}
          {expanded
            ? <ChevronUp className="w-4 h-4 text-gray-500" />
            : <ChevronDown className="w-4 h-4 text-gray-500" />
          }
        </div>
      </button>

      {/* Expandable form */}
      {expanded && (
        <div className="px-5 pb-5 space-y-3 border-t border-gray-800 pt-4 animate-fade-in">
          <p className="text-xs text-gray-500">
            Fill this once — ATS Score, Skill Gap, Interview Prep, and Job Matches all use it automatically.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Target Role *</label>
              <input
                className="input"
                placeholder="e.g. Senior ML Engineer"
                value={jobContext.targetRole}
                onChange={e => update('targetRole', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Experience Level</label>
              <select
                className="input"
                value={jobContext.experienceLevel}
                onChange={e => update('experienceLevel', e.target.value)}
              >
                <option value="junior">Junior (0-2 yrs)</option>
                <option value="mid">Mid-level (2-5 yrs)</option>
                <option value="senior">Senior (5-8 yrs)</option>
                <option value="lead">Lead / Principal (8+ yrs)</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Location</label>
              <input
                className="input"
                placeholder="e.g. Hyderabad / Remote"
                value={jobContext.location}
                onChange={e => update('location', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Remote Preference</label>
              <select
                className="input"
                value={jobContext.remotePreference}
                onChange={e => update('remotePreference', e.target.value)}
              >
                <option value="any">Any</option>
                <option value="remote">Remote Only</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site Only</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Job Description (paste from LinkedIn/Naukri/Indeed)</label>
            <textarea
              className="input min-h-[120px] resize-none"
              placeholder="Paste the full job description here..."
              value={jobContext.jobDescription}
              onChange={e => update('jobDescription', e.target.value)}
            />
            <p className="text-xs text-gray-600 mt-1">{jobContext.jobDescription.length} chars</p>
          </div>
          {jobContext.targetRole && (
            <div className="flex items-center gap-2 text-xs text-green-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Job context saved — all analysis sections will use this automatically
            </div>
          )}
        </div>
      )}
    </div>
  )
}
