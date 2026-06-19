/**
 * usePipeline — orchestrates the 3-step resume onboarding pipeline:
 * upload → extract text → generate embeddings
 *
 * Drives the store state machine so all components stay in sync.
 */

import { useCallback } from 'react'
import toast from 'react-hot-toast'
import { resumeApi } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'

export function usePipeline() {
  const { state, dispatch } = useResumeStore()

  const runPipeline = useCallback(async (file: File) => {
    dispatch({ type: 'SET_UPLOADING' })

    try {
      // Step 1: Upload
      const uploadToast = toast.loading('Uploading resume...')
      const uploaded = await resumeApi.upload(file)
      dispatch({
        type: 'SET_UPLOADED',
        resumeId: uploaded.resume_id,
        filename: uploaded.filename,
        fileSize: uploaded.file_size,
      })
      toast.success('Resume uploaded!', { id: uploadToast })

      // Step 2: Extract text & build structured profile
      const extractToast = toast.loading('Extracting and parsing resume...')
      const extracted = await resumeApi.extractText(uploaded.resume_id)
      dispatch({
        type: 'SET_EXTRACTED',
        profile: extracted.structured_profile,
        preview: extracted.preview,
      })
      toast.success('Resume parsed successfully!', { id: extractToast })

      // Step 3: Generate embeddings
      const embedToast = toast.loading('Generating AI embeddings...')
      await resumeApi.generateEmbeddings(uploaded.resume_id)
      dispatch({ type: 'SET_READY' })
      toast.success('Ready for AI analysis!', { id: embedToast })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Pipeline failed'
      dispatch({ type: 'SET_ERROR', error: message })
      toast.error(message)
    }
  }, [dispatch])

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' })
  }, [dispatch])

  return { state, runPipeline, reset }
}
