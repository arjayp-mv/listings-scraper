-- =============================================================================
-- Amazon Reviews Scraper - Database Schema
-- =============================================================================
-- Run this script in phpMyAdmin or MySQL CLI to set up the database
-- =============================================================================

-- Create database
CREATE DATABASE IF NOT EXISTS amazon_reviews_scraper
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE amazon_reviews_scraper;

-- =============================================================================
-- SKUs Table
-- =============================================================================
-- Purpose: Organize scrape jobs by product SKU (e.g., WF2, WF3)
-- =============================================================================
CREATE TABLE IF NOT EXISTS sku (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sku_code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_sku_code (sku_code)
) ENGINE=InnoDB;

-- =============================================================================
-- Scrape Jobs Table
-- =============================================================================
-- Purpose: Track each scraping job with its configuration and progress
-- =============================================================================
CREATE TABLE IF NOT EXISTS scrape_job (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sku_id BIGINT,
    job_name VARCHAR(255) NOT NULL,
    status ENUM('queued', 'running', 'completed', 'partial', 'failed', 'cancelled')
        DEFAULT 'queued',
    marketplace VARCHAR(10) DEFAULT 'com',
    sort_by VARCHAR(20) DEFAULT 'recent',
    max_pages INT DEFAULT 10,
    star_filters JSON,
    keyword_filter VARCHAR(255),
    reviewer_type VARCHAR(20) DEFAULT 'all_reviews',
    total_asins INT DEFAULT 0,
    completed_asins INT DEFAULT 0,
    failed_asins INT DEFAULT 0,
    total_reviews INT DEFAULT 0,
    apify_delay_seconds INT DEFAULT 10,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,

    FOREIGN KEY (sku_id) REFERENCES sku(id) ON DELETE SET NULL,
    INDEX idx_job_status (status),
    INDEX idx_job_sku (sku_id),
    INDEX idx_job_created (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- Job ASINs Table
-- =============================================================================
-- Purpose: Track each ASIN within a job and its scraping status
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_asin (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    asin VARCHAR(15) NOT NULL,
    product_title VARCHAR(500),
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    reviews_found INT DEFAULT 0,
    apify_run_id VARCHAR(50),
    error_message TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,

    FOREIGN KEY (job_id) REFERENCES scrape_job(id) ON DELETE CASCADE,
    INDEX idx_job_asin_status (status),
    INDEX idx_job_asin_job (job_id)
) ENGINE=InnoDB;

-- =============================================================================
-- Reviews Table
-- =============================================================================
-- Purpose: Store scraped reviews with full data for analysis
-- =============================================================================
CREATE TABLE IF NOT EXISTS review (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_asin_id BIGINT NOT NULL,
    review_id VARCHAR(50),
    title VARCHAR(500),
    text TEXT,
    rating VARCHAR(20),
    date VARCHAR(100),
    user_name VARCHAR(200),
    verified BOOLEAN DEFAULT FALSE,
    helpful_count INT DEFAULT 0,
    raw_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_asin_id) REFERENCES job_asin(id) ON DELETE CASCADE,
    UNIQUE KEY unique_review (review_id),
    INDEX idx_review_job_asin (job_asin_id),
    FULLTEXT INDEX idx_review_search (title, text)
) ENGINE=InnoDB;

-- =============================================================================
-- ASIN History Table
-- =============================================================================
-- Purpose: Track previously scraped ASINs to warn about duplicates
-- =============================================================================
CREATE TABLE IF NOT EXISTS asin_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asin VARCHAR(15) NOT NULL,
    marketplace VARCHAR(10) NOT NULL,
    last_scraped_job_id BIGINT,
    last_scraped_at TIMESTAMP,
    total_scrapes INT DEFAULT 1,

    UNIQUE KEY unique_asin_marketplace (asin, marketplace),
    FOREIGN KEY (last_scraped_job_id) REFERENCES scrape_job(id) ON DELETE SET NULL,
    INDEX idx_asin_history_asin (asin)
) ENGINE=InnoDB;

-- =============================================================================
-- Sample Data (Optional - Remove in Production)
-- =============================================================================
-- Uncomment below to insert sample SKU for testing
-- INSERT INTO sku (sku_code, description) VALUES
--     ('WF2', 'Water Filter Model 2 - Competitor Analysis'),
--     ('WF3', 'Water Filter Model 3 - Competitor Analysis');
