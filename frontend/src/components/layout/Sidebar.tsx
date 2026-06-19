/**
 * Application sidebar with navigation links and resume status.
 */

import { clsx } from 'clsx'
import {
  BarChart3,
  BookOpen,
  Briefcase,
  MessageSquare,
  RotateCcw,
  Settings,
  Star,
  Target,
  TrendingUp,
  Upload,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useResumeStore } from '../../store/resumeStore'

interface NavItem {
  to: string
  icon: React.ElementType
  label: string
  requiresResume?: boolean
}

const navItems: NavItem[] = [
  { to: '/',          icon: Upload,        label: 'Upload Resume' },
  { to: '/dashboard', icon: BarChart3,     label: 'Dashboard',      requiresResume: true },
  { to: '/ats',       icon: Target,        label: 'ATS Score',      requiresResume: true },
  { to: '/skill-gap', icon: BookOpen,      label: 'Skill Gap',      requiresResume: true },
  { to: '/interview', icon: Star,          label: 'Interview Prep', requiresResume: true },
  { to: '/career',    icon: TrendingUp,    label: 'Career Paths',   requiresResume: true },
  { to: '/jobs',      icon: Briefcase,     label: 'Job Matches',    requiresResume: true },
  { to: '/chat',      icon: MessageSquare, label: 'AI Chat',        requiresResume: true },
  { to: '/settings',  icon: Settings,      label: 'LLM Settings' },
]

export function Sidebar() {
  const { state, dispatch } = useResumeStore()
  const isReady = state.pipelineStep === 'ready'

  return (
    <aside className="w-64 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">CG</span>
          </div>
          <div>
            <h1 className="text-white font-bold text-base leading-none">CareerGPT</h1>
            <p className="text-gray-500 text-xs mt-0.5">AI Career Assistant</p>
          </div>
        </div>
      </div>

      {/* Resume status chip */}
      {state.filename && (
        <div className="mx-4 mt-4 px-3 py-2 bg-gray-800 rounded-lg border border-gray-700">
          <p className="text-xs text-gray-500 mb-0.5">Active Resume</p>
          <p className="text-sm text-gray-200 font-medium truncate">{state.filename}</p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className={clsx(
              'w-2 h-2 rounded-full',
              isReady ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'
            )} />
            <span className="text-xs text-gray-400">
              {isReady ? 'Ready for analysis' : 'Processing...'}
            </span>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(item => {
          const disabled = item.requiresResume && !isReady
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                  disabled
                    ? 'text-gray-600 cursor-not-allowed pointer-events-none'
                    : isActive
                    ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-600/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                )
              }
              onClick={e => disabled && e.preventDefault()}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </NavLink>
          )
        })}
      </nav>

      {/* Start Over button */}
      {state.resumeId && (
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={() => dispatch({ type: 'RESET' })}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500
                       hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Start Over
          </button>
        </div>
      )}
    </aside>
  )
}
