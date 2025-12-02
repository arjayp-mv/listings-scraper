# Playwright Testing Tasks - Amazon Reviews Scraper

## Test Configuration
- **SKU:** `HA-MAF1-FLT`
- **ASINs:** `B0893V5PYC`, `B0BG2J4NJ1` (2 ASINs)
- **Max Pages:** 3
- **URL:** `http://localhost:8080`

---

## Tasks

### Phase 0: Start Server
- [ ] Start backend server (`python -m src.main`)
- [ ] Verify server running at localhost:8080

### Phase 1: Dashboard & Navigation
- [ ] Navigate to http://localhost:8080
- [ ] Verify dashboard loads with stats cards
- [ ] Test navigation links (Dashboard, New Scrape, Jobs, SKUs)

### Phase 2: SKU Management
- [ ] Navigate to SKUs page
- [ ] Create SKU: `HA-MAF1-FLT` with description
- [ ] Verify SKU appears in table
- [ ] Edit SKU description
- [ ] Verify changes saved

### Phase 3: Create Scrape Job
- [ ] Navigate to New Scrape page
- [ ] Fill job name: "Playwright Test Job - HA-MAF1-FLT"
- [ ] Enter SKU code: `HA-MAF1-FLT`
- [ ] Paste ASINs: `B0893V5PYC`, `B0BG2J4NJ1`
- [ ] Set marketplace: amazon.com
- [ ] Set max pages: 3
- [ ] Select star filters: 5-star and 1-star
- [ ] Click "Start Scraping"
- [ ] Verify redirect to job detail page

### Phase 4: Job Monitoring
- [ ] Observe job status changes (queued → running → completed)
- [ ] Verify progress stats update
- [ ] Check ASINs tab shows individual progress
- [ ] Wait for job completion

### Phase 5: Reviews Features
- [ ] Click "Copy All Reviews" button
- [ ] Verify button shows "Copied!"
- [ ] Test search filter
- [ ] Test star rating filter
- [ ] Click "Download Excel"
- [ ] Click "Download JSON"

### Phase 6: Jobs List
- [ ] Navigate to Jobs page
- [ ] Verify created job in list
- [ ] Test status filter dropdown
- [ ] Click View to return to job detail

### Phase 7: Additional Operations
- [ ] Test Delete job (on a completed job)
- [ ] Verify job removed from list

### Phase 8: Edge Cases
- [ ] Test empty form submission (validation errors)
- [ ] Test form with no star filters selected
- [ ] Verify back links work

---

## Test Results

| Phase | Status | Notes |
|-------|--------|-------|
| 0. Start Server | ⏳ Pending | |
| 1. Dashboard | ⏳ Pending | |
| 2. SKU Management | ⏳ Pending | |
| 3. Create Job | ⏳ Pending | |
| 4. Job Monitoring | ⏳ Pending | |
| 5. Reviews | ⏳ Pending | |
| 6. Jobs List | ⏳ Pending | |
| 7. Additional Ops | ⏳ Pending | |
| 8. Edge Cases | ⏳ Pending | |

---

## Issues Found
*(Will be updated during testing)*

---

## Legend
- ⏳ Pending
- 🔄 In Progress
- ✅ Passed
- ❌ Failed
- ⚠️ Issue Found
