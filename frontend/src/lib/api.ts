/**
 * CareerGPT API Client
 * Typed axios wrapper for all backend endpoints.
 */

import axios, { AxiosError, AxiosResponse } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // AI calls can be slow
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor — normalise errors
apiClient.interceptors.response.use(
  (res: AxiosResponse) => res,
  (error: AxiosError<{ error?: string; detail?: string }>) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      'Something went wrong'
    return Promise.reject(new Error(message))
  }
)

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ResumeUploadResponse {
  resume_id: string
  filename: string
  file_size: number
  message: string
}

export interface StructuredProfile {
  name?: string
  email?: string
  phone?: string
  location?: string
  summary?: string
  skills: string[]
  technical_skills: string[]
  soft_skills: string[]
  experience: Array<{
    title: string
    company: string
    duration: string
    years?: number
    responsibilities: string[]
    technologies: string[]
  }>
  education: Array<{
    degree: string
    institution: string
    year?: number
    gpa?: number
  }>
  certifications: string[]
  languages: string[]
  projects: Array<{ name: string; description: string; technologies: string[] }>
  years_of_experience?: number
}

export interface ExtractTextResponse {
  resume_id: string
  text_length: number
  preview: string
  structured_profile: StructuredProfile
}

export interface GenerateEmbeddingsResponse {
  resume_id: string
  chunks_count: number
  collection_name: string
  message: string
}

export interface AnalyzeResumeResponse {
  resume_id: string
  profile_summary: string
  overall_quality_score: number
  strengths: string[]
  improvements: string[]
  formatting_feedback: string[]
  content_feedback: string[]
  recommended_sections: string[]
}

export interface ATSKeyword {
  keyword: string
  found: boolean
  importance: 'high' | 'medium' | 'low'
  context?: string
}

export interface ATSResponse {
  resume_id: string
  overall_score: number
  keyword_match_score: number
  format_score: number
  content_score: number
  keywords_found: string[]
  keywords_missing: string[]
  keyword_details: ATSKeyword[]
  recommendations: string[]
  summary: string
}

export interface SkillResource {
  name: string
  url?: string
  type: string
  duration?: string
  cost?: string
}

export interface SkillGap {
  skill: string
  current_level: string
  required_level: string
  priority: 'high' | 'medium' | 'low'
  learning_resources: SkillResource[]
}

export interface SkillGapResponse {
  resume_id: string
  target_role: string
  current_skills: string[]
  required_skills: string[]
  skill_gaps: SkillGap[]
  strengths: string[]
  roadmap: string[]
  estimated_time_to_ready: string
  certifications_recommended: string[]
}

export interface InterviewQuestion {
  id: number
  question: string
  type: string
  difficulty: string
  topic: string
  hint?: string
  sample_answer?: string
  evaluation_criteria: string[]
}

export interface InterviewResponse {
  resume_id: string
  target_role: string
  questions: InterviewQuestion[]
  preparation_tips: string[]
  common_pitfalls: string[]
}

export interface CareerPath {
  title: string
  description: string
  required_skills: string[]
  average_salary?: string
  growth_potential: string
  time_to_achieve: string
  steps: string[]
}

export interface CareerSuggestionsResponse {
  resume_id: string
  current_level: string
  career_paths: CareerPath[]
  industry_trends: string[]
  growth_opportunities: string[]
  action_plan: string[]
  networking_tips: string[]
}

export interface JobMatch {
  title: string
  company: string
  location: string
  match_percentage: number
  matching_skills: string[]
  missing_skills: string[]
  salary_range?: string
  job_type: string
  remote: boolean
  why_good_fit: string
  apply_url?: string
}

export interface JobRecommendationResponse {
  resume_id: string
  total_matches: number
  jobs: JobMatch[]
  search_strategy: string[]
}

export interface ChatResponse {
  session_id: string
  message: string
  sources: string[]
  suggested_actions: string[]
}

// ─── API Functions ────────────────────────────────────────────────────────────

export const resumeApi = {
  upload: async (file: File): Promise<ResumeUploadResponse> => {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<ResumeUploadResponse>('/upload-resume', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  extractText: async (resumeId: string): Promise<ExtractTextResponse> => {
    const res = await apiClient.post<ExtractTextResponse>('/extract-text', {
      resume_id: resumeId,
    })
    return res.data
  },

  generateEmbeddings: async (
    resumeId: string,
    forceRegenerate = false
  ): Promise<GenerateEmbeddingsResponse> => {
    const res = await apiClient.post<GenerateEmbeddingsResponse>('/generate-embeddings', {
      resume_id: resumeId,
      force_regenerate: forceRegenerate,
    })
    return res.data
  },

  analyzeResume: async (
    resumeId: string,
    targetRole?: string
  ): Promise<AnalyzeResumeResponse> => {
    const res = await apiClient.post<AnalyzeResumeResponse>('/analyze-resume', {
      resume_id: resumeId,
      target_role: targetRole,
    })
    return res.data
  },
}

export const analysisApi = {
  atsScore: async (
    resumeId: string,
    jobDescription: string,
    targetRole?: string
  ): Promise<ATSResponse> => {
    const res = await apiClient.post<ATSResponse>('/ats-score', {
      resume_id: resumeId,
      job_description: jobDescription,
      target_role: targetRole,
    })
    return res.data
  },

  skillGap: async (
    resumeId: string,
    targetRole: string,
    jobDescription?: string,
    experienceLevel?: string
  ): Promise<SkillGapResponse> => {
    const res = await apiClient.post<SkillGapResponse>('/skill-gap-analysis', {
      resume_id: resumeId,
      target_role: targetRole,
      job_description: jobDescription,
      experience_level: experienceLevel,
    })
    return res.data
  },

  interviewQuestions: async (params: {
    resumeId: string
    targetRole: string
    jobDescription?: string
    questionTypes?: string[]
    difficulty?: string
    numQuestions?: number
  }): Promise<InterviewResponse> => {
    const res = await apiClient.post<InterviewResponse>('/interview-questions', {
      resume_id: params.resumeId,
      target_role: params.targetRole,
      job_description: params.jobDescription,
      question_types: params.questionTypes ?? ['technical', 'behavioral'],
      difficulty: params.difficulty ?? 'medium',
      num_questions: params.numQuestions ?? 10,
    })
    return res.data
  },

  careerSuggestions: async (params: {
    resumeId: string
    currentRole?: string
    careerGoals?: string
    industryPreference?: string
    locationPreference?: string
  }): Promise<CareerSuggestionsResponse> => {
    const res = await apiClient.post<CareerSuggestionsResponse>('/career-suggestions', {
      resume_id: params.resumeId,
      current_role: params.currentRole,
      career_goals: params.careerGoals,
      industry_preference: params.industryPreference,
      location_preference: params.locationPreference,
    })
    return res.data
  },

  jobRecommendations: async (params: {
    resumeId: string
    targetRole?: string
    location?: string
    remotePreference?: string
    experienceLevel?: string
  }): Promise<JobRecommendationResponse> => {
    const res = await apiClient.post<JobRecommendationResponse>('/job-recommendations', {
      resume_id: params.resumeId,
      target_role: params.targetRole,
      location: params.location,
      remote_preference: params.remotePreference,
      experience_level: params.experienceLevel,
    })
    return res.data
  },
}

export const chatApi = {
  send: async (params: {
    resumeId: string
    message: string
    sessionId?: string
    history?: Array<{ role: string; content: string }>
  }): Promise<ChatResponse> => {
    const res = await apiClient.post<ChatResponse>('/chat', {
      resume_id: params.resumeId,
      message: params.message,
      session_id: params.sessionId,
      conversation_history: params.history ?? [],
    })
    return res.data
  },
}
