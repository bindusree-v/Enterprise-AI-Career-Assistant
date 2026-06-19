/**
 * Global state store — resume pipeline + shared job context.
 * Job context (role + JD) is entered ONCE and shared across ALL analysis pages.
 */

import React, { createContext, useContext, useReducer } from 'react'
import type {
  AnalyzeResumeResponse,
  ATSResponse,
  CareerSuggestionsResponse,
  InterviewResponse,
  JobRecommendationResponse,
  SkillGapResponse,
  StructuredProfile,
} from '../lib/api'

export type PipelineStep = 'idle' | 'uploading' | 'extracting' | 'embedding' | 'ready' | 'error'

export interface JobContext {
  targetRole: string
  jobDescription: string
  experienceLevel: string
  location: string
  remotePreference: string
}

export interface ResumeState {
  resumeId: string | null
  filename: string | null
  fileSize: number | null
  pipelineStep: PipelineStep
  pipelineError: string | null
  profile: StructuredProfile | null
  textPreview: string | null

  // Shared job context — entered once, used by all sections
  jobContext: JobContext

  // Cached analysis results
  analysisResult: AnalyzeResumeResponse | null
  atsResult: ATSResponse | null
  skillGapResult: SkillGapResponse | null
  interviewResult: InterviewResponse | null
  careerResult: CareerSuggestionsResponse | null
  jobResult: JobRecommendationResponse | null
  chatSessionId: string | null
}

const defaultJobContext: JobContext = {
  targetRole: '',
  jobDescription: '',
  experienceLevel: 'mid',
  location: '',
  remotePreference: 'any',
}

const initialState: ResumeState = {
  resumeId: null,
  filename: null,
  fileSize: null,
  pipelineStep: 'idle',
  pipelineError: null,
  profile: null,
  textPreview: null,
  jobContext: defaultJobContext,
  analysisResult: null,
  atsResult: null,
  skillGapResult: null,
  interviewResult: null,
  careerResult: null,
  jobResult: null,
  chatSessionId: null,
}

type Action =
  | { type: 'SET_UPLOADING' }
  | { type: 'SET_UPLOADED'; resumeId: string; filename: string; fileSize: number }
  | { type: 'SET_EXTRACTED'; profile: StructuredProfile; preview: string }
  | { type: 'SET_EMBEDDING' }
  | { type: 'SET_READY' }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'SET_JOB_CONTEXT'; context: Partial<JobContext> }
  | { type: 'SET_ANALYSIS'; result: AnalyzeResumeResponse }
  | { type: 'SET_ATS'; result: ATSResponse }
  | { type: 'SET_SKILL_GAP'; result: SkillGapResponse }
  | { type: 'SET_INTERVIEW'; result: InterviewResponse }
  | { type: 'SET_CAREER'; result: CareerSuggestionsResponse }
  | { type: 'SET_JOBS'; result: JobRecommendationResponse }
  | { type: 'SET_CHAT_SESSION'; sessionId: string }
  | { type: 'RESET' }

function reducer(state: ResumeState, action: Action): ResumeState {
  switch (action.type) {
    case 'SET_UPLOADING':
      return { ...initialState, pipelineStep: 'uploading' }
    case 'SET_UPLOADED':
      return { ...state, resumeId: action.resumeId, filename: action.filename, fileSize: action.fileSize, pipelineStep: 'extracting' }
    case 'SET_EXTRACTED':
      return { ...state, profile: action.profile, textPreview: action.preview, pipelineStep: 'embedding' }
    case 'SET_EMBEDDING':
      return { ...state, pipelineStep: 'embedding' }
    case 'SET_READY':
      return { ...state, pipelineStep: 'ready' }
    case 'SET_ERROR':
      return { ...state, pipelineStep: 'error', pipelineError: action.error }
    case 'SET_JOB_CONTEXT':
      return { ...state, jobContext: { ...state.jobContext, ...action.context } }
    case 'SET_ANALYSIS':
      return { ...state, analysisResult: action.result }
    case 'SET_ATS':
      return { ...state, atsResult: action.result }
    case 'SET_SKILL_GAP':
      return { ...state, skillGapResult: action.result }
    case 'SET_INTERVIEW':
      return { ...state, interviewResult: action.result }
    case 'SET_CAREER':
      return { ...state, careerResult: action.result }
    case 'SET_JOBS':
      return { ...state, jobResult: action.result }
    case 'SET_CHAT_SESSION':
      return { ...state, chatSessionId: action.sessionId }
    case 'RESET':
      return initialState
    default:
      return state
  }
}

interface ResumeContextValue {
  state: ResumeState
  dispatch: React.Dispatch<Action>
}

const ResumeContext = createContext<ResumeContextValue | null>(null)

export function ResumeProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return (
    <ResumeContext.Provider value={{ state, dispatch }}>
      {children}
    </ResumeContext.Provider>
  )
}

export function useResumeStore() {
  const ctx = useContext(ResumeContext)
  if (!ctx) throw new Error('useResumeStore must be used within ResumeProvider')
  return ctx
}
