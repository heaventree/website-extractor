/*
  # WebReconstruct Extraction Storage

  1. New Tables
    - `extractions` - stores crawl metadata and summary
    - `extracted_pages` - stores individual page data with markdown/json

  2. Features
    - Full-site crawl tracking with stats (pages, words, assets)
    - Per-page extraction data (title, content, markdown, json)
    - Extraction ownership via user_id
    - Auto-timestamping and status tracking

  3. Security
    - Enable RLS on both tables
    - Users can only view/edit their own extractions
    - Automatic user_id population from auth context
*/

CREATE TABLE IF NOT EXISTS extractions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  url text NOT NULL,
  mode text NOT NULL CHECK (mode IN ('single', 'full')),
  depth integer DEFAULT 1,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'partial')),
  title text,
  description text,
  total_pages integer DEFAULT 0,
  total_words integer DEFAULT 0,
  total_images integer DEFAULT 0,
  total_links integer DEFAULT 0,
  failed_pages integer DEFAULT 0,
  num_packs integer DEFAULT 0,
  duration_seconds integer,
  error_message text,
  created_at timestamptz DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS extracted_pages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  extraction_id uuid NOT NULL REFERENCES extractions(id) ON DELETE CASCADE,
  url text NOT NULL,
  title text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'extracting', 'success', 'failed')),
  status_message text,
  word_count integer DEFAULT 0,
  image_count integer DEFAULT 0,
  link_count integer DEFAULT 0,
  markdown_content text,
  json_content jsonb,
  pack_number integer DEFAULT 1,
  page_number integer,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_pages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own extractions"
  ON extractions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own extractions"
  ON extractions FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own extractions"
  ON extractions FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own extractions"
  ON extractions FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view pages from own extractions"
  ON extracted_pages FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM extractions
      WHERE extractions.id = extracted_pages.extraction_id
      AND extractions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert pages to own extractions"
  ON extracted_pages FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM extractions
      WHERE extractions.id = extracted_pages.extraction_id
      AND extractions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update pages in own extractions"
  ON extracted_pages FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM extractions
      WHERE extractions.id = extracted_pages.extraction_id
      AND extractions.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM extractions
      WHERE extractions.id = extracted_pages.extraction_id
      AND extractions.user_id = auth.uid()
    )
  );

CREATE INDEX idx_extractions_user_id ON extractions(user_id);
CREATE INDEX idx_extractions_created_at ON extractions(created_at DESC);
CREATE INDEX idx_extracted_pages_extraction_id ON extracted_pages(extraction_id);
CREATE INDEX idx_extracted_pages_status ON extracted_pages(status);
