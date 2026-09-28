/*
# Create WeatherGPT tables (single-tenant, no auth)

1. New Tables
- `user_preferences`: Stores user configuration including language, units, notification toggles, data source selection, accessibility settings, and offline storage info.
  - `id` (uuid, primary key, defaults to gen_random_uuid)
  - `language` (text, default 'en') — interface language code
  - `temperature_unit` (text, default 'C') — 'C' or 'F'
  - `wind_speed_unit` (text, default 'kmh') — 'kmh', 'ms', 'kts', or 'mph'
  - `data_source` (text, default 'IMD') — primary weather data source
  - `red_alert_push` (boolean, default true) — red warning push alerts toggle
  - `severe_sirens` (boolean, default true) — severe weather audio sirens toggle
  - `sms_fallback` (boolean, default false) — low-bandwidth SMS fallback toggle
  - `high_contrast` (boolean, default false) — high contrast mode toggle
  - `large_font` (boolean, default false) — large font scaling toggle
  - `dark_mode` (boolean, default false) — dark mode theme toggle
  - `farmer_mode` (boolean, default false) — farmer advisory mode toggle
  - `sync_interval` (integer, default 30) — WIS 2.0 sync interval in minutes
  - `cache_size_mb` (integer, default 142) — radar & map cache size in MB
  - `cache_limit_mb` (integer, default 500) — cache limit in MB
  - `updated_at` (timestamptz, default now())

- `chat_messages`: Stores AI chat conversation history for the Ask AI feature.
  - `id` (uuid, primary key, defaults to gen_random_uuid)
  - `role` (text, not null) — 'user' or 'assistant'
  - `content` (text, not null) — message content
  - `language` (text, default 'en') — language the message was sent in
  - `created_at` (timestamptz, default now())

2. Security
- Enable RLS on both tables.
- Allow anon + authenticated CRUD because the data is intentionally shared/public (single-tenant app with demo login).
*/

CREATE TABLE IF NOT EXISTS user_preferences (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  language text DEFAULT 'en',
  temperature_unit text DEFAULT 'C',
  wind_speed_unit text DEFAULT 'kmh',
  data_source text DEFAULT 'IMD',
  red_alert_push boolean DEFAULT true,
  severe_sirens boolean DEFAULT true,
  sms_fallback boolean DEFAULT false,
  high_contrast boolean DEFAULT false,
  large_font boolean DEFAULT false,
  dark_mode boolean DEFAULT false,
  farmer_mode boolean DEFAULT false,
  sync_interval integer DEFAULT 30,
  cache_size_mb integer DEFAULT 142,
  cache_limit_mb integer DEFAULT 500,
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_preferences" ON user_preferences;
CREATE POLICY "anon_select_preferences" ON user_preferences FOR SELECT
  TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_preferences" ON user_preferences;
CREATE POLICY "anon_insert_preferences" ON user_preferences FOR INSERT
  TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_preferences" ON user_preferences;
CREATE POLICY "anon_update_preferences" ON user_preferences FOR UPDATE
  TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_preferences" ON user_preferences;
CREATE POLICY "anon_delete_preferences" ON user_preferences FOR DELETE
  TO anon, authenticated USING (true);

CREATE TABLE IF NOT EXISTS chat_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  role text NOT NULL,
  content text NOT NULL,
  language text DEFAULT 'en',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_chat" ON chat_messages;
CREATE POLICY "anon_select_chat" ON chat_messages FOR SELECT
  TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_chat" ON chat_messages;
CREATE POLICY "anon_insert_chat" ON chat_messages FOR INSERT
  TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_chat" ON chat_messages;
CREATE POLICY "anon_delete_chat" ON chat_messages FOR DELETE
  TO anon, authenticated USING (true);
