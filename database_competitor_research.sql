-- =============================================================================
-- Competitor Research Feature - Database Migration
-- Amazon Reviews Scraper
-- =============================================================================

USE amazon_reviews_scraper;

-- =============================================================================
-- 1. Update existing sku table - add display_name
-- =============================================================================
ALTER TABLE sku
    ADD COLUMN display_name VARCHAR(255) NULL AFTER sku_code;

-- =============================================================================
-- 2. Update existing channel_sku table - add pack_size
-- =============================================================================
ALTER TABLE channel_sku
    ADD COLUMN pack_size INT NULL DEFAULT 1 AFTER current_asin;

-- =============================================================================
-- 3. Competitors Table - Individual competitor ASINs being tracked
-- =============================================================================
CREATE TABLE IF NOT EXISTS competitor (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sku_id BIGINT NULL,
    asin VARCHAR(15) NOT NULL,
    marketplace VARCHAR(10) NOT NULL DEFAULT 'com',
    pack_size INT NULL DEFAULT 1,
    display_name VARCHAR(255) NULL,
    schedule ENUM('none', 'daily', 'every_2_days', 'every_3_days', 'weekly', 'monthly') DEFAULT 'none',
    next_scrape_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (sku_id) REFERENCES sku(id) ON DELETE SET NULL,
    UNIQUE KEY unique_competitor_asin_marketplace (asin, marketplace),
    INDEX idx_competitor_sku_id (sku_id),
    INDEX idx_competitor_schedule (schedule, next_scrape_at),
    INDEX idx_competitor_active (is_active),
    INDEX idx_competitor_marketplace (marketplace)
) ENGINE=InnoDB;

-- =============================================================================
-- 4. Competitor Data Table - Latest Scraped Data (1:1 with competitor)
-- =============================================================================
CREATE TABLE IF NOT EXISTS competitor_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    competitor_id BIGINT NOT NULL,
    title VARCHAR(500) NULL,
    brand VARCHAR(255) NULL,
    manufacturer VARCHAR(255) NULL,
    price DECIMAL(10,2) NULL,
    retail_price DECIMAL(10,2) NULL,
    shipping_price DECIMAL(10,2) NULL,
    currency VARCHAR(10) NULL,
    unit_price DECIMAL(10,4) NULL,
    price_saving VARCHAR(100) NULL,
    rating DECIMAL(2,1) NULL,
    review_count INT NULL,
    past_sales VARCHAR(100) NULL,
    availability VARCHAR(100) NULL,
    sold_by VARCHAR(255) NULL,
    fulfilled_by VARCHAR(255) NULL,
    seller_id VARCHAR(50) NULL,
    is_prime BOOLEAN DEFAULT FALSE,
    features JSON NULL,
    product_description TEXT NULL,
    main_image_url VARCHAR(500) NULL,
    images JSON NULL,
    videos JSON NULL,
    categories JSON NULL,
    variations JSON NULL,
    variations_count INT DEFAULT 0,
    product_details JSON NULL,
    review_insights JSON NULL,
    raw_data JSON NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (competitor_id) REFERENCES competitor(id) ON DELETE CASCADE,
    UNIQUE KEY unique_competitor_data (competitor_id),
    INDEX idx_competitor_data_scraped (scraped_at)
) ENGINE=InnoDB;

-- =============================================================================
-- 5. Competitor Price History Table (1 year retention)
-- =============================================================================
CREATE TABLE IF NOT EXISTS competitor_price_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    competitor_id BIGINT NOT NULL,
    price DECIMAL(10,2) NULL,
    unit_price DECIMAL(10,4) NULL,
    shipping_price DECIMAL(10,2) NULL,
    availability VARCHAR(100) NULL,
    rating DECIMAL(2,1) NULL,
    review_count INT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (competitor_id) REFERENCES competitor(id) ON DELETE CASCADE,
    INDEX idx_price_history_competitor (competitor_id),
    INDEX idx_price_history_scraped (scraped_at),
    INDEX idx_price_history_comp_date (competitor_id, scraped_at DESC)
) ENGINE=InnoDB;

-- =============================================================================
-- 6. Competitor Keywords Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS competitor_keyword (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sku_id BIGINT NULL,
    keyword VARCHAR(255) NOT NULL,
    marketplace VARCHAR(10) NOT NULL DEFAULT 'com',
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (sku_id) REFERENCES sku(id) ON DELETE SET NULL,
    INDEX idx_keyword_sku_id (sku_id),
    INDEX idx_keyword_marketplace (marketplace),
    INDEX idx_keyword_text (keyword)
) ENGINE=InnoDB;

-- =============================================================================
-- 7. Keyword-Channel SKU Links Table (Many-to-Many)
-- =============================================================================
CREATE TABLE IF NOT EXISTS keyword_channel_sku_link (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword_id BIGINT NOT NULL,
    channel_sku_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (keyword_id) REFERENCES competitor_keyword(id) ON DELETE CASCADE,
    FOREIGN KEY (channel_sku_id) REFERENCES channel_sku(id) ON DELETE CASCADE,
    UNIQUE KEY unique_keyword_channel_sku (keyword_id, channel_sku_id),
    INDEX idx_link_keyword (keyword_id),
    INDEX idx_link_channel_sku (channel_sku_id)
) ENGINE=InnoDB;

-- =============================================================================
-- 8. Keyword-Competitor Links Table (Many-to-Many)
-- =============================================================================
CREATE TABLE IF NOT EXISTS keyword_competitor_link (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword_id BIGINT NOT NULL,
    competitor_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (keyword_id) REFERENCES competitor_keyword(id) ON DELETE CASCADE,
    FOREIGN KEY (competitor_id) REFERENCES competitor(id) ON DELETE CASCADE,
    UNIQUE KEY unique_keyword_competitor (keyword_id, competitor_id),
    INDEX idx_link_keyword_comp (keyword_id),
    INDEX idx_link_competitor (competitor_id)
) ENGINE=InnoDB;

-- =============================================================================
-- 9. Competitor Scrape Jobs Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS competitor_scrape_job (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    status ENUM('queued', 'running', 'completed', 'partial', 'failed', 'cancelled') DEFAULT 'queued',
    job_type ENUM('manual', 'scheduled') DEFAULT 'manual',
    marketplace VARCHAR(10) NOT NULL DEFAULT 'com',
    total_competitors INT DEFAULT 0,
    completed_competitors INT DEFAULT 0,
    failed_competitors INT DEFAULT 0,
    error_message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,

    INDEX idx_comp_job_status (status),
    INDEX idx_comp_job_created (created_at DESC)
) ENGINE=InnoDB;

-- =============================================================================
-- 10. Competitor Scrape Items Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS competitor_scrape_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    competitor_id BIGINT NOT NULL,
    input_asin VARCHAR(15) NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT NULL,
    apify_run_id VARCHAR(50) NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,

    FOREIGN KEY (job_id) REFERENCES competitor_scrape_job(id) ON DELETE CASCADE,
    FOREIGN KEY (competitor_id) REFERENCES competitor(id) ON DELETE CASCADE,
    INDEX idx_comp_item_job_status (job_id, status),
    INDEX idx_comp_item_competitor (competitor_id)
) ENGINE=InnoDB;

-- =============================================================================
-- End of Migration Script
-- =============================================================================
