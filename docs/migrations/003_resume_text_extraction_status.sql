-- Phase 3: explicit status after raw text has been extracted successfully

ALTER TYPE public.resume_processing_status
ADD VALUE IF NOT EXISTS 'text_extracted'
AFTER 'extracting_text';
