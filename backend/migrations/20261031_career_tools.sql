-- Additive migration for CareerLens career tools and comparison history.
-- Run against the existing CareerLens schema before deploying in production.

CREATE TABLE IF NOT EXISTS candidate_profiles (
    user_id VARCHAR(36) NOT NULL PRIMARY KEY,
    country_code VARCHAR(8) NOT NULL DEFAULT 'IN',
    country_name VARCHAR(80) NOT NULL DEFAULT 'India',
    city VARCHAR(120) NOT NULL DEFAULT '',
    currency_code VARCHAR(8) NOT NULL DEFAULT 'INR',
    time_zone VARCHAR(64) NOT NULL DEFAULT 'Asia/Kolkata',
    education_level VARCHAR(120) NOT NULL DEFAULT '',
    preferred_roles JSON NOT NULL,
    skill_interests JSON NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_candidate_profiles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS job_applications (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    job_title VARCHAR(180) NOT NULL,
    company VARCHAR(180) NOT NULL DEFAULT '',
    location VARCHAR(180) NOT NULL DEFAULT '',
    posting_url VARCHAR(2048) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'saved',
    notes TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_job_applications_user_id (user_id),
    CONSTRAINT fk_job_applications_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS analysis_runs (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    resume_id VARCHAR(36) NOT NULL,
    baseline_run_id VARCHAR(36) NULL,
    target_role VARCHAR(120) NOT NULL,
    input_fingerprint CHAR(64) NOT NULL,
    run_kind VARCHAR(24) NOT NULL DEFAULT 'baseline',
    overall_coverage FLOAT NULL,
    skill_coverage FLOAT NULL,
    matched_skills JSON NOT NULL,
    missing_skills JSON NOT NULL,
    score_components JSON NOT NULL,
    evidence_summary JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_analysis_runs_user_id (user_id),
    INDEX ix_analysis_runs_resume_id (resume_id),
    INDEX ix_analysis_runs_input_fingerprint (input_fingerprint),
    CONSTRAINT fk_analysis_runs_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_analysis_runs_resume FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE,
    CONSTRAINT fk_analysis_runs_baseline FOREIGN KEY (baseline_run_id) REFERENCES analysis_runs (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS interview_sessions (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    resume_id VARCHAR(36) NOT NULL,
    target_role VARCHAR(120) NOT NULL,
    focus_skills JSON NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    final_report TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    INDEX ix_interview_sessions_user_id (user_id),
    INDEX ix_interview_sessions_resume_id (resume_id),
    CONSTRAINT fk_interview_sessions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_interview_sessions_resume FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS interview_turns (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    turn_number INT NOT NULL,
    question TEXT NOT NULL,
    category VARCHAR(32) NOT NULL,
    focus_skill VARCHAR(120) NOT NULL,
    answer TEXT NULL,
    evaluation JSON NULL,
    score FLOAT NULL,
    evaluated_by VARCHAR(24) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_interview_turn_number (session_id, turn_number),
    INDEX ix_interview_turns_session_id (session_id),
    CONSTRAINT fk_interview_turns_session FOREIGN KEY (session_id) REFERENCES interview_sessions (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
