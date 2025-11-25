#!/bin/bash

###############################################################################
# Run All Scrapers Script
# This script runs both TunisiaNet and MyTek scrapers sequentially
###############################################################################

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/price_comparator"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Log file
LOG_FILE="$SCRIPT_DIR/scraper.log"

echo -e "${GREEN}=== Running All Scrapers ===${NC}" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"

# Activate virtual environment
source venv/bin/activate

# Run TunisiaNet scraper
echo -e "\n${YELLOW}[1/2] Running TunisiaNet scraper...${NC}" | tee -a "$LOG_FILE"
scrapy crawl tunisianet 2>&1 | tee -a "$LOG_FILE"
TUNISIANET_STATUS=${PIPESTATUS[0]}

if [ $TUNISIANET_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ TunisiaNet scraper completed successfully${NC}" | tee -a "$LOG_FILE"
else
    echo -e "${RED}✗ TunisiaNet scraper failed with exit code $TUNISIANET_STATUS${NC}" | tee -a "$LOG_FILE"
fi

# Small delay between scrapers
sleep 5

# Run MyTek scraper
echo -e "\n${YELLOW}[2/2] Running MyTek scraper...${NC}" | tee -a "$LOG_FILE"
scrapy crawl mytek 2>&1 | tee -a "$LOG_FILE"
MYTEK_STATUS=${PIPESTATUS[0]}

if [ $MYTEK_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ MyTek scraper completed successfully${NC}" | tee -a "$LOG_FILE"
else
    echo -e "${RED}✗ MyTek scraper failed with exit code $MYTEK_STATUS${NC}" | tee -a "$LOG_FILE"
fi

# Deactivate virtual environment
deactivate

# Summary
echo -e "\n${GREEN}=== Scraping Complete ===${NC}" | tee -a "$LOG_FILE"
echo "Finished at: $(date)" | tee -a "$LOG_FILE"

# Get product count
if command -v mongosh &> /dev/null; then
    PRODUCT_COUNT=$(mongosh product_comparator --quiet --eval "db.products.countDocuments()" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "Total products in database: ${GREEN}$PRODUCT_COUNT${NC}" | tee -a "$LOG_FILE"
    fi
fi

# Exit with error if any scraper failed
if [ $TUNISIANET_STATUS -ne 0 ] || [ $MYTEK_STATUS -ne 0 ]; then
    exit 1
fi

exit 0
