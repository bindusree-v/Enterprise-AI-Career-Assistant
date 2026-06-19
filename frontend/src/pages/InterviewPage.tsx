/**
 * Interview Prep — uses shared job context (role + JD) automatically.
 * User only picks difficulty and question count.
 */

import { clsx } from 'clsx'
import { ChevronDown, ChevronUp, Lightbulb, Star } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { analysisApi, type InterviewQuestion } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'
import { JobContextPanel } from '../components/ui/JobContextPanel'
import { FullPageLoader } from '../components/ui/LoadingSpinner'

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'badge-green', medium: 'badge-yellow', hard: 'badge-red',
}
const TYPE_COLORS: Record<string, string> = {
  technical: 'badge-blue', behavioral: 'badge-purple', situational: 'badge-yellow',
}

function QuestionCard({ q, index }: { q: InterviewQuestion; index: number }) {
  const [showAnswer, setShowAnswer] = useState(false)
  const [showHint, setShowHint] = useState(false)
  return (
    <div className="border border-gray-800 rounded-xl p-5 space-y-3 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-600/40 flex items-center justify-center text-indigo-400 text-xs font-bold">
            {index + 1}
          </span>
          <p className="text-gray-200 font-medium text-sm leading-relaxed">{q.question}</p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <span className={`badge ${TYPE_COLORS[q.type] ?? 'badge-blue'}`}>{q.type}</span>
          <span className={`badge ${DIFFICULTY_COLORS[q.difficulty] ?? 'badge-yellow'}`}>{q.difficulty}</span>
        </div>
      </div>
      <p className="text-xs text-gray-500 ml-10">📌 {q.topic}</p>
      <div className="ml-10 flex gap-3 flex-wrap">
        {q.hint && (
          <button onClick={() => setShowHint(o => !o)} className="flex items-center gap-1 text-xs text-yellow-400 hover:text-yellow-300">
            <Lightbulb className="w-3 h-3" />{showHint ? 'Hide Hint' : 'Show Hint'}
          </button>
        )}
        {q.sample_answer && (
          <button onClick={() => setShowAnswer(o => !o)} className="flex items-center gap-1 text-xs text-green-400 hover:text-green-300">
            {showAnswer ? <><ChevronUp className="w-3 h-3" />Hide Answer</> : <><ChevronDown className="w-3 h-3" />Show Sample Answer</>}
          </button>
        )}
      </div>
      {showHint && q.hint && (
        <div className="ml-10 p-3 bg-yellow-900/20 border border-yellow-800 rounded-lg text-sm text-yellow-200 animate-fade-in">
          💡 {q.hint}
        </div>
      )}
      {showAnswer && q.sample_answer && (
        <div className="ml-10 p-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-300 animate-fade-in">
          <p className="text-xs text-gray-500 mb-1 font-medium">Sample Answer:</p>
          {q.sample_answer}
        </div>
      )}
    </div>
  )
}

export function InterviewPage() {
  const { state, dispatch } = useResumeStore()
  const { jobContext } = state
  const [difficulty, setDifficulty] = useState('medium')
  const [numQuestions, setNumQuestions] = useState(10)
  const [questionTypes, setQuestionTypes] = useState<string[]>(['technical', 'behavioral'])
  const [loading, setLoading] = useState(false)
  const result = state.interviewResult

  const toggleType = (type: string) =>
    setQuestionTypes(prev => prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type])

  const handleGenerate = async () => {
    if (!jobContext.targetRole) {
      toast.error('Set your Target Role in the Job Context panel above')
      return
    }
    setLoading(true)
    try {
      const data = await analysisApi.interviewQuestions({
        resumeId: state.resumeId!,
        targetRole: jobContext.targetRole,
        jobDescription: jobContext.jobDescription || undefined,
        questionTypes,
        difficulty,
        numQuestions,
      })
      dispatch({ type: 'SET_INTERVIEW', result: data })
      toast.success(`${data.questions.length} questions generated!`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Failed to generate questions')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <FullPageLoader label="Crafting personalized questions..." />

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Star className="w-6 h-6 text-yellow-400" />
          Interview Prep
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Personalized questions based on your resume and target role.
        </p>
      </div>

      <JobContextPanel />

      {/* Interview-specific options only */}
      <div className="card space-y-4">
        <h3 className="text-sm font-semibold text-gray-300">Interview Options</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Difficulty</label>
            <select className="input" value={difficulty} onChange={e => setDifficulty(e.target.value)}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">
              Number of Questions: <span className="text-white">{numQuestions}</span>
            </label>
            <input type="range" min={5} max={25} step={5} value={numQuestions}
              onChange={e => setNumQuestions(Number(e.target.value))}
              className="w-full accent-indigo-500" />
          </div>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-2 block">Question Types</label>
          <div className="flex gap-3">
            {['technical', 'behavioral', 'situational'].map(type => (
              <button key={type} onClick={() => toggleType(type)}
                className={clsx(
                  'px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors capitalize',
                  questionTypes.includes(type)
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                )}>
                {type}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        className="btn-primary w-full md:w-auto px-8"
        onClick={handleGenerate}
        disabled={!jobContext.targetRole}
      >
        Generate {numQuestions} Questions
      </button>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="card space-y-4">
            <h2 className="section-title">{result.questions.length} Questions for {result.target_role}</h2>
            <div className="space-y-4">
              {result.questions.map((q, i) => <QuestionCard key={q.id} q={q} index={i} />)}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {result.preparation_tips.length > 0 && (
              <div className="card">
                <h2 className="section-title text-base">✅ Preparation Tips</h2>
                <ul className="space-y-2">
                  {result.preparation_tips.map((tip, i) => (
                    <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-green-400">•</span>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.common_pitfalls.length > 0 && (
              <div className="card">
                <h2 className="section-title text-base">⚠️ Common Pitfalls</h2>
                <ul className="space-y-2">
                  {result.common_pitfalls.map((p, i) => (
                    <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-red-400">•</span>{p}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
