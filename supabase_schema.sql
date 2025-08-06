-- Supabase database schema for Sapyyn Patient Referral System
-- This schema replaces the NoCodeBackend collections with PostgreSQL tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create referrals table (replaces NoCodeBackend referrals collection)
CREATE TABLE IF NOT EXISTS referrals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    referral_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    patient_id INTEGER,
    dentist_id INTEGER,
    patient_name VARCHAR(255) NOT NULL,
    referring_doctor VARCHAR(255),
    target_doctor VARCHAR(255),
    medical_condition TEXT,
    urgency_level VARCHAR(50) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'pending',
    case_status VARCHAR(50) DEFAULT 'pending',
    consultation_date TIMESTAMPTZ,
    case_accepted_date TIMESTAMPTZ,
    treatment_start_date TIMESTAMPTZ,
    treatment_complete_date TIMESTAMPTZ,
    rejection_reason TEXT,
    estimated_value DECIMAL(10,2),
    actual_value DECIMAL(10,2),
    notes TEXT,
    qr_code TEXT,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create documents table (replaces NoCodeBackend uploads collection)
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    referral_id UUID REFERENCES referrals(id) ON DELETE CASCADE,
    user_id INTEGER,
    file_type VARCHAR(100) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500),
    file_size BIGINT,
    content_type VARCHAR(100),
    upload_date TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_referrals_user_id ON referrals(user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);
CREATE INDEX IF NOT EXISTS idx_referrals_created_at ON referrals(created_at);
CREATE INDEX IF NOT EXISTS idx_referrals_patient_name ON referrals(patient_name);
CREATE INDEX IF NOT EXISTS idx_referrals_referring_doctor ON referrals(referring_doctor);
CREATE INDEX IF NOT EXISTS idx_referrals_target_doctor ON referrals(target_doctor);

CREATE INDEX IF NOT EXISTS idx_documents_referral_id ON documents(referral_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);

-- Create full-text search indexes for referrals
CREATE INDEX IF NOT EXISTS idx_referrals_search_patient ON referrals 
    USING gin(to_tsvector('english', patient_name));
CREATE INDEX IF NOT EXISTS idx_referrals_search_condition ON referrals 
    USING gin(to_tsvector('english', medical_condition));
CREATE INDEX IF NOT EXISTS idx_referrals_search_notes ON referrals 
    USING gin(to_tsvector('english', notes));

-- Create a function to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update updated_at columns
DROP TRIGGER IF EXISTS update_referrals_updated_at ON referrals;
CREATE TRIGGER update_referrals_updated_at
    BEFORE UPDATE ON referrals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies for security
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own referrals
CREATE POLICY "Users can view their own referrals" ON referrals
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert their own referrals" ON referrals
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update their own referrals" ON referrals
    FOR UPDATE USING (auth.uid()::text = user_id::text);

-- Policy: Users can only see their own documents
CREATE POLICY "Users can view their own documents" ON documents
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert their own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update their own documents" ON documents
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete their own documents" ON documents
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Create storage buckets (run these commands in Supabase dashboard or using the client)
-- These are just documentation of what needs to be created in Supabase Storage:
-- 
-- Bucket: documents
-- - Public: false
-- - File size limit: 50MB
-- - Allowed MIME types: image/*, application/pdf, text/*, application/msword, 
--   application/vnd.openxmlformats-officedocument.wordprocessingml.document
-- 
-- Bucket: uploads
-- - Public: false  
-- - File size limit: 50MB
-- - Allowed MIME types: image/*, application/pdf, text/*

-- Sample data for testing (optional)
-- INSERT INTO referrals (referral_id, user_id, patient_name, referring_doctor, target_doctor, medical_condition, status, notes)
-- VALUES 
-- ('REF001', 1, 'John Doe', 'Dr. Smith', 'Dr. Johnson', 'Routine dental checkup', 'pending', 'Patient needs routine cleaning and examination'),
-- ('REF002', 1, 'Jane Smith', 'Dr. Brown', 'Dr. Wilson', 'Tooth extraction needed', 'pending', 'Wisdom tooth extraction required');

-- Comments for documentation
COMMENT ON TABLE referrals IS 'Patient referrals data - replaces NoCodeBackend referrals collection';
COMMENT ON TABLE documents IS 'Document metadata and file references - replaces NoCodeBackend uploads collection';
COMMENT ON COLUMN referrals.referral_id IS 'Unique referral identifier displayed to users';
COMMENT ON COLUMN referrals.user_id IS 'ID of the user who created the referral';
COMMENT ON COLUMN referrals.qr_code IS 'Base64 encoded QR code for the referral';
COMMENT ON COLUMN documents.file_url IS 'Public URL of the file in Supabase Storage';
COMMENT ON COLUMN documents.file_path IS 'Path to the file in the storage bucket';